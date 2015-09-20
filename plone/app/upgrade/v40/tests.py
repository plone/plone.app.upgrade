import time

from zope.component import getMultiAdapter
from zope.component import getSiteManager
from zope.component import getUtility
from zope.component import queryUtility
from zope.ramcache.interfaces.ram import IRAMCache

from Products.CMFCore.ActionInformation import Action
from Products.CMFCore.Expression import Expression
from Products.CMFCore.utils import getToolByName
from Products.MailHost.interfaces import IMailHost

from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.v40.alphas import _KNOWN_ACTION_ICONS
from plone.app.upgrade.v40.alphas import migrateActionIcons
from plone.app.upgrade.v40.alphas import migrateTypeIcons
from plone.app.upgrade.v40.alphas import addOrReplaceRamCache
from plone.app.upgrade.v40.alphas import changeWorkflowActorVariableExpression
from plone.app.upgrade.v40.alphas import changeAuthenticatedResourcesCondition
from plone.app.upgrade.v40.alphas import setupReferencebrowser
from plone.app.upgrade.v40.alphas import migrateMailHost
from plone.app.upgrade.v40.alphas import migrateFolders
from plone.app.upgrade.v40.alphas import renameJoinFormFields
from plone.app.upgrade.v40.alphas import updateLargeFolderType
from plone.app.upgrade.v40.alphas import addRecursiveGroupsPlugin
from plone.app.upgrade.v40.alphas import cleanUpClassicThemeResources
from plone.app.upgrade.v40.alphas import migrateStaticTextPortlets
from plone.app.upgrade.v40.betas import repositionRecursiveGroupsPlugin
from plone.app.upgrade.v40.betas import updateIconMetadata
from plone.app.upgrade.v40.betas import removeLargePloneFolder
from plone.app.upgrade.tests.base import MigrationTest
from plone.app.upgrade.utils import version_match

from plone.portlet.static import static
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import IPortletAssignmentSettings
from plone.portlets.interfaces import IPortletManager


class FakeSecureMailHost(object):

    meta_type = 'Secure Mail Host'
    id = 'MailHost'
    title = 'Fake MailHost'
    smtp_host = 'smtp.example.com'
    smtp_port = 587
    smtp_userid='me'
    smtp_pass='secret'
    smtp_notls=False

    def manage_fixupOwnershipAfterAdd(self):
        pass


class TestMigrations_v4_0alpha1(MigrationTest):

    profile = "profile-plone.app.upgrade.v40:3-4alpha1"

    def afterSetUp(self):
        self.atool = getToolByName(self.portal, 'portal_actions')
        self.cptool = getToolByName(self.portal, 'portal_controlpanel')
        self.wftool = getToolByName(self.portal, 'portal_workflow')
        self.csstool = getToolByName(self.portal, 'portal_css')
        self.jstool = getToolByName(self.portal, 'portal_javascripts')

        if 'portal_actionicons' not in self.portal:
            from plone.app.upgrade.bbb import ActionIconsTool
            self.portal._setObject('portal_actionicons', ActionIconsTool())
        self.aitool = self.portal.portal_actionicons

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        self.setRoles(['Manager'])
        loadMigrationProfile(self.portal, self.profile)
        self.assertTrue(True)

    def testMigrateActionIcons(self):
        _KNOWN_ACTION_ICONS['object_buttons'].extend(['test_id', 'test2_id'])
        self.aitool.addActionIcon(
            category='object_buttons',
            action_id='test_id',
            icon_expr='test.gif',
            title='Test my icon',
            )
        self.aitool.addActionIcon(
            category='object_buttons',
            action_id='test2_id',
            icon_expr='python:context.getIcon()',
            title='Test my second icon',
            )
        test_action = Action('test_id',
            title='Test me',
            description='',
            url_expr='',
            icon_expr='',
            available_expr='',
            permissions=('View', ),
            visible = True)
        test2_action = Action('test2_id',
            title='Test me too',
            description='',
            url_expr='',
            icon_expr='',
            available_expr='',
            permissions=('View', ),
            visible = True)

        object_buttons = self.atool.object_buttons
        if getattr(object_buttons, 'test_id', None) is None:
            object_buttons._setObject('test_id', test_action)
        if getattr(object_buttons, 'test2_id', None) is None:
            object_buttons._setObject('test2_id', test2_action)

        self.assertEqual(object_buttons.test_id.icon_expr, '')
        self.assertEqual(object_buttons.test2_id.icon_expr, '')
        # Test it twice
        for i in range(2):
            migrateActionIcons(self.portal)
            icons = [ic._action_id for ic in self.aitool.listActionIcons()]
            self.assertFalse('test_id' in icons)
            self.assertFalse('test2_id' in icons)
            self.assertEqual(object_buttons.test_id.icon_expr,
                             'string:$portal_url/test.gif')
            self.assertEqual(object_buttons.test2_id.icon_expr,
                             'python:context.getIcon()')

    def testMigrateControlPanelActionIcons(self):
        _KNOWN_ACTION_ICONS['controlpanel'].extend(['test_id'])
        self.aitool.addActionIcon(
            category='controlpanel',
            action_id='test_id',
            icon_expr='test.gif',
            title='Test my icon',
            )

        self.cptool.registerConfiglet(
            id='test_id',
            name='Test Configlet',
            action='string:${portal_url}/test',
            permission='Manage portal',
            category='Plone',
            visible=True,
            appId='',
            icon_expr='',
            )

        action = self.cptool.getActionObject('Plone/test_id')
        self.assertEqual(action.getIconExpression(), '')
        # Test it twice
        for i in range(2):
            migrateActionIcons(self.portal)
            icons = [ic._action_id for ic in self.aitool.listActionIcons()]
            self.assertFalse('test_id' in icons)
            self.assertEqual(action.getIconExpression(),
                             'string:$portal_url/test.gif')

    def testContentTypeIconExpressions(self):
        """
        FTIs should now be using icon_expr instead of content_icon.
        (The former caches the expression object.)
        """
        tt = getToolByName(self.portal, "portal_types")
        tt.Document.icon_expr = None
        loadMigrationProfile(self.portal, self.profile, ('typeinfo', ))
        self.assertEqual(tt.Document.icon_expr,
                         "string:${portal_url}/document_icon.png")

    def testMigrateTypeIcons(self):
        """
        FTIs having content_icon should be upgraded to icon_expr.
        """
        tt = getToolByName(self.portal, "portal_types")
        del tt.Document.icon_expr
        tt.Document.content_icon = 'document_icon.gif'
        migrateTypeIcons(self.portal)
        self.assertEqual(tt.Document.icon_expr,
                         "string:${portal_url}/document_icon.gif")
        self.assertTrue(hasattr(tt.Document, 'icon_expr_object'))

        #Don't upgrade if there is already an icon_expr.
        tt.Document.icon_expr = "string:${portal_url}/document_icon.png"
        tt.Document.content_icon = 'document_icon.gif'
        migrateTypeIcons(self.portal)
        self.assertEqual(tt.Document.icon_expr,
                         "string:${portal_url}/document_icon.png")

    def testPngContentIcons(self):
        tt = getToolByName(self.portal, "portal_types")
        tt.Document.icon_expr = "string:${portal_url}/document_icon.gif"
        loadMigrationProfile(self.portal, self.profile, ('typeinfo', ))
        self.assertEqual(tt.Document.icon_expr,
            "string:${portal_url}/document_icon.png")

    def testAddRAMCache(self):
        # Test it twice
        for i in range(2):
            sm = getSiteManager()
            sm.unregisterUtility(provided=IRAMCache)
            util = queryUtility(IRAMCache)
            self.assertEqual(util.maxAge, 86400)
            addOrReplaceRamCache(self.portal)
            util = queryUtility(IRAMCache)
            self.assertEqual(util.maxAge, 3600)

    def testReplaceOldRamCache(self):
        sm = getSiteManager()

        # Test it twice
        for i in range(2):
            sm.unregisterUtility(provided=IRAMCache)
            from zope.app.cache.interfaces.ram import IRAMCache as OldIRAMCache
            from zope.app.cache.ram import RAMCache as OldRAMCache
            sm.registerUtility(factory=OldRAMCache, provided=OldIRAMCache)

            addOrReplaceRamCache(self.portal)
            util = queryUtility(IRAMCache)
            self.assertEqual(util.maxAge, 3600)

    def testChangeWorkflowActorVariableExpression(self):
        self.wftool.intranet_folder_workflow.variables.actor.setProperties('')

        for i in range(2):
            changeWorkflowActorVariableExpression(self.portal)
            wf = self.wftool.intranet_folder_workflow
            self.assertEqual(wf.variables.actor.getDefaultExprText(),
                             'user/getId')
            wf = self.wftool.one_state_workflow
            self.assertEqual(wf.variables.actor.getDefaultExprText(),
                             'user/getId')
            wf = self.wftool.simple_publication_workflow
            self.assertEqual(wf.variables.actor.getDefaultExprText(),
                             'user/getId')

        # make sure it doesn't break if the workflow is missing
        wf = self.wftool.intranet_folder_workflow
        self.wftool._delOb('intranet_folder_workflow')
        changeWorkflowActorVariableExpression(self.portal)
        self.wftool._setOb('intranet_folder_workflow', wf)

    def testChangeAuthenticatedResourcesCondition(self):
        # make sure CSS resource is updated
        res = self.csstool.getResource('member.css')
        if res is None:
            return
        res.setAuthenticated(False)
        res.setExpression('not: portal/portal_membership/isAnonymousUser')
        # test it twice
        for i in range(2):
            changeAuthenticatedResourcesCondition(self.portal)
            self.assertEqual(res.getExpression(), '')
            self.assertTrue(res.getAuthenticated())

        # make sure it doesn't update it if the expression has been
        # customized
        res.setExpression('python:False')
        changeAuthenticatedResourcesCondition(self.portal)
        self.assertEqual(res.getExpression(), 'python:False')

    def testAddedUseEmailProperty(self):
        tool = getToolByName(self.portal, 'portal_properties')
        sheet = getattr(tool, 'site_properties')
        #self.assertEqual(sheet.getProperty('use_email_as_login'), False)
        self.removeSiteProperty('use_email_as_login')
        loadMigrationProfile(self.portal, self.profile, ('propertiestool', ))
        self.assertEqual(sheet.getProperty('use_email_as_login'), False)

    def testReplaceReferencebrowser(self):
        self.setRoles(['Manager'])
        skins_tool = getToolByName(self.portal, 'portal_skins')
        if 'referencebrowser' not in skins_tool:
            return
        sels = skins_tool._getSelections()
        for skinname, layer in sels.items():
            layers = layer.split(',')
            self.assertFalse('ATReferenceBrowserWidget' in layers)
            layers.remove('referencebrowser')
            new_layers = ','.join(layers)
            sels[skinname] = new_layers

        from .alphas import threeX_alpha1
        threeX_alpha1(self.portal)
        setupReferencebrowser(self.portal)

        sels = skins_tool._getSelections()
        for skinname, layer in sels.items():
            layers = layer.split(',')
            self.assertTrue('referencebrowser' in layers)

    def testInstallNewDependencies(self):
        from plone.app.upgrade.v40.alphas import threeX_alpha1
        self.setRoles(['Manager'])
        # test for running the TinyMCE profile by checking for the skin layer
        # it installs (the profile is marked as noninstallable, so we can't
        # ask the quick installer)
        skins_tool = getToolByName(self.portal, 'portal_skins')
        if 'tinymce' not in skins_tool:
            # Skip test in new Plones that don't have tinymce to begin with
            return
        del skins_tool['tinymce']
        for i in range(2):
            threeX_alpha1(self.portal)
            self.assertTrue('tinymce' in skins_tool)
            # sleep to avoid a GS log filename collision :-o
            time.sleep(1)

    def testReplaceSecureMailHost(self):
        portal = self.portal
        sm = getSiteManager(context=portal)
        # try it with an unmodified site to ensure it doesn't give any errors
        migrateMailHost(portal.portal_setup)
        portal._delObject('MailHost')
        # Run it with our MailHost replaced
        portal._setObject('MailHost', FakeSecureMailHost())
        self.assertEqual(portal.MailHost.meta_type, 'Secure Mail Host')
        sm.unregisterUtility(provided=IMailHost)
        sm.registerUtility(portal.MailHost, provided=IMailHost)
        migrateMailHost(portal)
        new_mh = portal.MailHost
        self.assertEqual(new_mh.meta_type, 'Mail Host')
        self.assertEqual(new_mh.title, 'Fake MailHost')
        self.assertEqual(new_mh.smtp_host, 'smtp.example.com')
        self.assertEqual(new_mh.smtp_port, 587)
        self.assertEqual(new_mh.smtp_uid, 'me')
        self.assertEqual(new_mh.smtp_pwd, 'secret')
        #Force TLS is always false, because SMH has no equivalent option
        self.assertEqual(new_mh.force_tls, False)

    def testFolderMigration(self):
        from plone.app.folder.tests.content import create
        from plone.app.folder.tests.test_migration import reverseMigrate
        from plone.app.folder.tests.test_migration import isSaneBTreeFolder
        # create a folder in an unmigrated state & check it's broken...
        folder = create('Folder', self.portal, 'foo', title='Foo')
        reverseMigrate(self.portal)
        self.assertFalse(isSaneBTreeFolder(self.portal.foo))
        # now run the migration step...
        migrateFolders(self.portal)
        folder = self.portal.foo
        self.assertTrue(isSaneBTreeFolder(folder))
        self.assertEqual(folder.getId(), 'foo')
        self.assertEqual(folder.Title(), 'Foo')

    def testMigrateStaticTextPortlets(self):
        class HiddenAssignment(static.Assignment):
            hide = True

        self.setRoles(["Manager"])
        self.portal.invokeFactory('Folder', id="statictest")
        folder = self.portal['statictest']

        manager = getUtility(
                IPortletManager, name='plone.rightcolumn',
                context=folder)
        assignments = getMultiAdapter(
                (folder, manager), IPortletAssignmentMapping)
        hidden_portlet = HiddenAssignment()
        visible_portlet = static.Assignment()
        assignments['hidden'] = hidden_portlet
        assignments['visible'] = visible_portlet

        migrateStaticTextPortlets(self.portal)

        self.assertFalse(
                IPortletAssignmentSettings(hidden_portlet).get(
                        'visible', True))
        self.assertTrue(
                IPortletAssignmentSettings(visible_portlet).get(
                        'visible', True))



class TestMigrations_v4_0alpha2(MigrationTest):

    def testMigrateJoinFormFields(self):
        ptool = getToolByName(self.portal, 'portal_properties')
        sheet = getattr(ptool, 'site_properties')
        self.removeSiteProperty('user_registration_fields')
        self.addSiteProperty('join_form_fields')
        sheet.join_form_fields = (
            'username', 'password', 'email', 'mail_me', 'groups')
        renameJoinFormFields(self)
        self.assertEqual(sheet.hasProperty('join_form_fields'), False)
        self.assertEqual(sheet.hasProperty('user_registration_fields'), True)
        self.assertEqual(sheet.getProperty('user_registration_fields'),
                         ('username', 'password', 'email', 'mail_me'))


class TestMigrations_v4_0alpha3(MigrationTest):

    profile = "profile-plone.app.upgrade.v40:4alpha2-4alpha3"

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.assertTrue(True)

    def testJoinActionURL(self):
        self.portal.portal_actions.user.join.url_expr = 'foo'
        loadMigrationProfile(self.portal, self.profile, ('actions', ))
        self.assertEqual(self.portal.portal_actions.user.join.url_expr,
            'string:${globals_view/navigationRootUrl}/@@register')


class TestMigrations_v4_0alpha5(MigrationTest):

    profile = "profile-plone.app.upgrade.v40:4alpha4-4alpha5"

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.assertTrue(True)

    def testMigrateLargeFolderType(self):
        portal = self.portal
        catalog = getToolByName(portal, 'portal_catalog')
        # set things up in the old way...
        ids = 'news', 'events', 'Members'
        for id in ids:
            obj = portal[id]
            obj._setPortalTypeName('Large Plone Folder')
            obj.reindexObject()
            self.assertEqual(obj.portal_type, 'Large Plone Folder')
            # Type falls back to meta_type since there's no
            # Large Plone Folder FTI
            self.assertEqual(obj.Type(), 'ATFolder')
            brain, = catalog(getId=id)
            self.assertEqual(brain.portal_type, 'Large Plone Folder')
            self.assertEqual(brain.Type, 'ATFolder')
        # migrate & check again...
        updateLargeFolderType(self.portal)
        for id in ids:
            obj = portal[id]
            self.assertEqual(obj.portal_type, 'Folder')
            self.assertEqual(obj.Type(), 'Folder')
            brain, = catalog(getId=id)
            self.assertEqual(brain.portal_type, 'Folder')
            self.assertEqual(brain.Type, 'Folder')

    def testAddRecursiveGroupsPlugin(self):
        acl = getToolByName(self.portal, 'acl_users')
        addRecursiveGroupsPlugin(self.portal)
        self.assertTrue('recursive_groups' in acl)
        # Now that we have an existing one, let's make sure it's handled
        # properly if this migration is run again.
        addRecursiveGroupsPlugin(self.portal)
        self.assertTrue('recursive_groups' in acl)

    def testClassicThemeResourcesCleanUp(self):
        """Test that the plonetheme.classic product doesn't have any
        registered CSS resource in its metadata after migration.
        """
        portal = self.portal
        qi = getToolByName(portal, 'portal_quickinstaller')
        qi.installProduct('plonetheme.classic')
        classictheme = qi['plonetheme.classic']
        classictheme.resources_css = ['something'] # add a random resource
        cleanUpClassicThemeResources(portal)
        self.assertEqual(classictheme.resources_css, [])

    def testGetObjPositionInParentIndex(self):
        from plone.app.folder.nogopip import GopipIndex
        catalog = self.portal.portal_catalog
        catalog.delIndex('getObjPositionInParent')
        catalog.addIndex('getObjPositionInParent', 'FieldIndex')
        self.assertFalse(isinstance(catalog.Indexes['getObjPositionInParent'],
            GopipIndex))
        loadMigrationProfile(self.portal, self.profile)
        self.assertTrue('getObjPositionInParent' in catalog.indexes())
        self.assertTrue(isinstance(catalog.Indexes['getObjPositionInParent'],
            GopipIndex))

    def testGetEventTypeIndex(self):
        catalog = self.portal.portal_catalog
        catalog.addIndex('getEventType', 'KeywordIndex')
        self.assertTrue('getEventType' in catalog.indexes())
        loadMigrationProfile(self.portal, self.profile)
        self.assertFalse('getEventType' in catalog.indexes())


class TestMigrations_v4_0beta1(MigrationTest):

    profile = "profile-plone.app.upgrade.v40:4alpha5-4beta1"

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.assertTrue(True)

    def testRepositionRecursiveGroupsPlugin(self):
        # Ensure that the recursive groups plugin is moved to the bottom
        # of the IGroups plugins list, if active.
        addRecursiveGroupsPlugin(self.portal)
        # Plugin is installed, but not active, run against this state.
        from Products.PluggableAuthService.interfaces.plugins import \
            IGroupsPlugin
        acl = getToolByName(self.portal, 'acl_users')
        plugins = acl.plugins
        # The plugin was originally moved to the top of the list of
        # IGroupsPlugin plugins by p.a.controlpanel. Recreate that state.
        while (plugins.getAllPlugins('IGroupsPlugin')['active'].index(
               'recursive_groups') > 0):
            plugins.movePluginsUp(IGroupsPlugin, ['recursive_groups'])

        active_groups = plugins.getAllPlugins('IGroupsPlugin')['active']
        self.assertEqual(active_groups[0], 'recursive_groups')

        # Rerun the migration, making sure that it's now the last item in the
        # list of IGroupsPlugin plugins.
        repositionRecursiveGroupsPlugin(self.portal)
        active_groups = plugins.getAllPlugins('IGroupsPlugin')['active']
        self.assertEqual(active_groups[-1], 'recursive_groups')


class TestMigrations_v4_0beta2(MigrationTest):

    profile = "profile-plone.app.upgrade.v40:4beta1-4beta2"

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.assertTrue(True)

    def testCoreContentIconExprCleared(self):
        types = getToolByName(self.portal, 'portal_types')
        catalog = getToolByName(self.portal, 'portal_catalog')
        # Reinstate the now-empty icon expression for the Document type
        doc_icon_expr = Expression('string:${portal_url}/document_icon.png')
        types['Document'].icon_expr_object = doc_icon_expr
        front = self.portal['front-page']
        catalog.reindexObject(front)
        old_modified = front.modified()
        # Make sure the getIcon metadata column shows the "original" value
        brains = catalog(id='front-page')
        self.assertEqual(brains[0].getIcon, 'document_icon.png')
        # Run the migration
        loadMigrationProfile(self.portal, self.profile)
        updateIconMetadata(self.portal)
        # The getIcon column should now be empty
        self.assertEqual(catalog(id='front-page')[0].getIcon, '')
        self.assertEqual(front.modified(), old_modified)


class TestMigrations_v4_0beta4(MigrationTest):

    profile = 'profile-plone.app.upgrade.v40:4beta3-4beta4'

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.assertTrue(True)

    def testRemoveLargePloneFolder(self):
        # re-create pre-migration settings
        ptool = self.portal.portal_properties
        nav_props = ptool.navtree_properties
        if not nav_props.hasProperty('parentMetaTypesNotToQuery'):
            return
        l = list(nav_props.parentMetaTypesNotToQuery)
        nav_props.parentMetaTypesNotToQuery = l + ['Large Plone Folder']
        site_props = ptool.site_properties
        l = list(site_props.typesLinkToFolderContentsInFC)
        site_props.typesLinkToFolderContentsInFC = l + ['Large Plone Folder']
        temp_folder_fti = self.portal.portal_types['TempFolder']
        l = list(temp_folder_fti.allowed_content_types)
        temp_folder_fti.allowed_content_types = l + ['Large Plone Folder']
        l = set(self.portal.portal_factory.getFactoryTypes())
        l.add('Large Plone Folder')
        ftool = self.portal.portal_factory
        ftool.manage_setPortalFactoryTypes(listOfTypeIds=list(l))

        for i in xrange(2):
            loadMigrationProfile(self.portal, self.profile)
            removeLargePloneFolder(self.portal)
            self.assertFalse('Large Plone Folder' in self.portal.portal_types)
            self.assertFalse('Large Plone Folder' in
                        temp_folder_fti.allowed_content_types)
            self.assertTrue('Folder' in temp_folder_fti.allowed_content_types)
            self.assertFalse('Large Plone Folder' in ftool.getFactoryTypes())
            self.assertTrue('Folder' in ftool.getFactoryTypes())
            self.assertFalse('Large Plone Folder' in
                        nav_props.parentMetaTypesNotToQuery)
            self.assertTrue('TempFolder' in
                            nav_props.parentMetaTypesNotToQuery)
            self.assertFalse('Large Plone Folder' in
                        site_props.typesLinkToFolderContentsInFC)
            self.assertTrue('Folder' in
                            site_props.typesLinkToFolderContentsInFC)
            # sleep to avoid a GS log filename collision :-o
            time.sleep(1)


class TestMigrations_v4_0beta5(MigrationTest):

    profile = 'profile-plone.app.upgrade.v40:4beta4-4beta5'

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.assertTrue(True)


class TestMigrations_v4_0rc1(MigrationTest):

    profile = 'profile-plone.app.upgrade.v40:4beta5-4rc1'

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.assertTrue(True)

class TestMigrations_v4_0(MigrationTest):

    profile = 'profile-plone.app.upgrade.v40:4rc1-4final'

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.assertTrue(True)

class TestMigrations_v4_0_1(MigrationTest):

    profile = 'profile-plone.app.upgrade.v40:4.0-4.0.1'

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.assertTrue(True)

class TestMigrations_v4_0_2(MigrationTest):

    profile = 'profile-plone.app.upgrade.v40:4.0.1-4.0.2'

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.assertTrue(True)

class TestMigrations_v4_0_3(MigrationTest):

    profile = 'profile-plone.app.upgrade.v40:4.0.2-4.0.3'

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.assertTrue(True)

class TestMigrations_v4_0_4(MigrationTest):

    profile = 'profile-plone.app.upgrade.v40:4.0.3-4.0.4'

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.assertTrue(True)

class TestMigrations_v4_0_5(MigrationTest):

    profile = 'profile-plone.app.upgrade.v40:4.0.4-4.0.5'

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.assertTrue(True)


def test_suite():
    import unittest
    if not version_match('4.0'):
        return unittest.TestSuite()
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
