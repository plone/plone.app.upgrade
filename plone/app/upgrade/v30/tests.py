from Acquisition import aq_base

from five.localsitemanager.registry import FiveVerifyingAdapterLookup

from plone.contentrules.engine.interfaces import IRuleStorage
from plone.app.i18n.locales.interfaces import IContentLanguages
from plone.app.i18n.locales.interfaces import ICountries
from plone.app.i18n.locales.interfaces import IMetadataLanguages
from plone.app.portlets import portlets
from plone.app.redirector.interfaces import IRedirectionStorage
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import ILocalPortletAssignmentManager
from plone.portlets.constants import CONTEXT_CATEGORY as CONTEXT_PORTLETS

from zExceptions import BadRequest
from zope.location.interfaces import ISite
from zope.component import getGlobalSiteManager
from zope.component import getSiteManager
from zope.component import getUtility, getMultiAdapter
from zope.component.hooks import clearSite

from Products.Archetypes.interfaces import IArchetypeTool
from Products.Archetypes.interfaces import IReferenceCatalog
from Products.Archetypes.interfaces import IUIDCatalog
from Products.CMFActionIcons.interfaces import IActionIconsTool
from Products.CMFCalendar.interfaces import ICalendarTool
from Products.CMFCore.ActionInformation import Action
from Products.CMFCore.ActionInformation import ActionCategory
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import getToolInterface
from Products.CMFCore.Expression import Expression
from Products.CMFCore.permissions import AccessInactivePortalContent
from Products.CMFCore.interfaces import IActionsTool
from Products.CMFCore.interfaces import ICachingPolicyManager
from Products.CMFCore.interfaces import ICatalogTool
from Products.CMFCore.interfaces import IContentTypeRegistry
from Products.CMFCore.interfaces import IDiscussionTool
from Products.CMFCore.interfaces import IMemberDataTool
from Products.CMFCore.interfaces import IMembershipTool
from Products.CMFCore.interfaces import IMetadataTool
from Products.CMFCore.interfaces import IPropertiesTool
from Products.CMFCore.interfaces import IRegistrationTool
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.interfaces import ISkinsTool
from Products.CMFCore.interfaces import ISyndicationTool
from Products.CMFCore.interfaces import ITypesTool
from Products.CMFCore.interfaces import IURLTool
from Products.CMFCore.interfaces import IConfigurableWorkflowTool
from Products.CMFCore.ActionInformation import ActionInformation
from Products.CMFDiffTool.interfaces import IDiffTool
from Products.CMFEditions.interfaces import IArchivistTool
from Products.CMFEditions.interfaces import IPortalModifierTool
from Products.CMFEditions.interfaces import IPurgePolicyTool
from Products.CMFEditions.interfaces.IRepository import IRepositoryTool
from Products.CMFEditions.interfaces import IStorageTool
from Products.CMFFormController.interfaces import IFormControllerTool
from Products.CMFQuickInstallerTool.interfaces import IQuickInstallerTool
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.interfaces import IPloneTool
from Products.CMFPlone.interfaces import ITranslationServiceTool
from Products.CMFUid.interfaces import IUniqueIdAnnotationManagement
from Products.CMFUid.interfaces import IUniqueIdGenerator
from Products.CMFUid.interfaces import IUniqueIdHandler
from Products.GenericSetup.interfaces import ISetupTool
from Products.MailHost.interfaces import IMailHost
from Products.MimetypesRegistry.interfaces import IMimetypesRegistryTool
from Products.PortalTransforms.interfaces import IPortalTransformsTool
from Products.PloneLanguageTool.interfaces import ILanguageTool
from Products.PlonePAS.interfaces.group import IGroupTool
from Products.PlonePAS.interfaces.group import IGroupDataTool
from Products.ResourceRegistries.interfaces import ICSSRegistry
from Products.ResourceRegistries.interfaces import IJSRegistry

from plone.app.upgrade.tests.base import FunctionalUpgradeTestCase
from plone.app.upgrade.tests.base import MigrationTest
from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.utils import version_match

from plone.app.upgrade.v30.alphas import enableZope3Site
from plone.app.upgrade.v30.alphas import migrateOldActions
from plone.app.upgrade.v30.alphas import updateActionsI18NDomain
from plone.app.upgrade.v30.alphas import updateFTII18NDomain
from plone.app.upgrade.v30.alphas import convertLegacyPortlets
from plone.app.upgrade.v30.alphas import registerToolsAsUtilities
from plone.app.upgrade.v30.alphas import registration
from plone.app.upgrade.v30.alphas import addReaderAndEditorRoles
from plone.app.upgrade.v30.alphas import migrateLocalroleForm
from plone.app.upgrade.v30.alphas import reorderUserActions
from plone.app.upgrade.v30.alphas import updatePASPlugins
from plone.app.upgrade.v30.alphas import updateConfigletTitles
from plone.app.upgrade.v30.alphas import updateMemberSecurity
from plone.app.upgrade.v30.alphas import addCacheForResourceRegistry
from plone.app.upgrade.v30.alphas import removeTablelessSkin
from plone.app.upgrade.v30.alphas import addObjectProvidesIndex
from plone.app.upgrade.v30.alphas import restorePloneTool
from plone.app.upgrade.v30.alphas import installProduct

from plone.app.upgrade.v30.betas import migrateHistoryTab
from plone.app.upgrade.v30.betas import changeOrderOfActionProviders
from plone.app.upgrade.v30.betas import cleanupOldActions
from plone.app.upgrade.v30.betas import cleanDefaultCharset
from plone.app.upgrade.v30.betas import addAutoGroupToPAS
from plone.app.upgrade.v30.betas import removeS5Actions
from plone.app.upgrade.v30.betas import addContributorToCreationPermissions
from plone.app.upgrade.v30.betas import removeSharingAction
from plone.app.upgrade.v30.betas import addEditorToSecondaryEditorPermissions
from plone.app.upgrade.v30.betas import updateEditActionConditionForLocking
from plone.app.upgrade.v30.betas import addOnFormUnloadJS

from plone.app.upgrade.v30.betas import updateTopicTitle
from plone.app.upgrade.v30.betas import cleanupActionProviders
from plone.app.upgrade.v30.betas import hidePropertiesAction

from plone.app.upgrade.v30.rcs import addIntelligentText

from plone.app.upgrade.v30.final_three0x import installNewModifiers

try:
    from Products.ATContentTypes.interface import IATCTTool
    HAS_ATCT = True
except ImportError:
    HAS_ATCT = False

try:
    from Products.CMFPlone.interfaces import IFactoryTool
except:
    from Products.ATContentTypes.interfaces import IFactoryTool


class TestMigrations_v3_0_Actions(MigrationTest):

    def afterSetUp(self):
        self.actions = self.portal.portal_actions
        self.types = self.portal.portal_types
        self.workflow = self.portal.portal_workflow
        self._migrate_reply_action()

    def _migrate_reply_action(self):
        # Create dummy old ActionInformation
        reply = ActionInformation('reply',
            title='Reply',
            category='reply_actions',
            condition='context/replyAllowed',
            permissions=(AccessInactivePortalContent, ),
            priority=10,
            visible=True,
            action='context/reply'
        )

        from OFS.SimpleItem import SimpleItem
        class DummyTool(SimpleItem):
            pass
        dummy = DummyTool()
        dummy._actions = (reply,)
        self.portal._setObject('dummy', dummy)

    def testMigrateActions(self):
        # Test it twice
        for i in range(2):
            migrateOldActions(self.portal)
            reply_actions = getattr(self.actions, 'reply_actions', None)
            self.assertFalse(reply_actions is None)
            reply = getattr(reply_actions, 'reply', None)
            self.assertFalse(reply is None)
            self.assertTrue(isinstance(reply, Action))
            # Verify all data has been upgraded correctly to the new Action
            data = reply.getInfoData()[0]
            self.assertEqual(data['category'], 'reply_actions')
            self.assertEqual(data['title'], 'Reply')
            self.assertEqual(data['visible'], True)
            self.assertEqual(data['permissions'], (AccessInactivePortalContent, ))
            self.assertEqual(data['available'].text, 'context/replyAllowed')
            self.assertEqual(data['url'].text, 'context/reply')
            # Make sure the original action has been removed
            self.assertEqual(len(self.portal.dummy._actions), 0)

    def testUpdateActionsI18NDomain(self):
        migrateOldActions(self.portal)
        reply = self.actions.reply_actions.reply
        self.assertEqual(reply.i18n_domain, '')
        # Test it twice
        for i in range(2):
            updateActionsI18NDomain(self.portal)
            self.assertEqual(reply.i18n_domain, 'plone')

    def testUpdateActionsI18NDomainNonAscii(self):
        migrateOldActions(self.portal)
        reply = self.actions.reply_actions.reply
        reply.title = 'Foo\xc3'
        self.assertEqual(reply.i18n_domain, '')
        self.assertEqual(reply.title, 'Foo\xc3')

        updateActionsI18NDomain(self.portal)

        self.assertEqual(reply.i18n_domain, '')

    def testHistoryActionID(self):
        # Test it twice
        for i in range(2):
            migrateHistoryTab(self.portal)
            objects = getattr(self.actions, 'object', None)
            self.assertFalse('rss' in objects.objectIds())

    def testProviderCleanup(self):
        self.actions.addActionProvider("portal_membership")
        self.assertTrue("portal_membership" in self.actions.listActionProviders())
        # Test it twice
        for i in range(2):
            cleanupActionProviders(self.portal)
            self.assertFalse("portal_membership" in self.actions.listActionProviders())

    def testRemovePropertiesActions(self):
        ti = self.types.getTypeInfo("Document")
        if ti.getActionObject("object/properties") is None:
            ti.addAction("metadata", "name", "action", "condition",
                    "permission", "object",)
        # Test it twice
        for i in range(2):
            hidePropertiesAction(self.portal)
            self.assertTrue(ti.getActionObject("object/metadata") is None)

    def tearDown(self):
        self.portal._delObject('dummy')


class TestMigrations_v2_5_x(MigrationTest):

    def afterSetUp(self):
        self.profile = 'profile-plone.app.upgrade.v30:2.5.x-3.0a1'
        self.types = self.portal.portal_types
        self.properties = self.portal.portal_properties

        for legacy_tool in ('portal_discussion', 'portal_actionicons'):
            if legacy_tool not in self.portal:
                from OFS.SimpleItem import SimpleItem
                self.portal._setObject(legacy_tool, SimpleItem())

    def disableSite(self, obj, iface=ISite):
        # We need our own disableSite method as the CMF portal implements
        # ISite directly, so we cannot remove it, like the disableSite method
        # in Five.component would have done
        from ZPublisher.BeforeTraverse import unregisterBeforeTraverse
        from Products.Five.component import HOOK_NAME
        obj = aq_base(obj)
        if not iface.providedBy(obj):
            raise TypeError('Object must be a site.')
        unregisterBeforeTraverse(obj, HOOK_NAME)
        if hasattr(obj, HOOK_NAME):
            delattr(obj, HOOK_NAME)

    def testEnableZope3Site(self):
        # First we remove the site and site manager
        self.disableSite(self.portal)
        clearSite(self.portal)
        self.portal.setSiteManager(None)
        gsm = getGlobalSiteManager()
        # Test it twice
        for i in range(2):
            enableZope3Site(self.portal)
            # And see if we have an ISite with a local site manager
            self.assertTrue(ISite.providedBy(self.portal))
            sm = getSiteManager(self.portal)
            self.assertFalse(gsm is sm)
            lc = sm.utilities.LookupClass
            self.assertEqual(lc, FiveVerifyingAdapterLookup)

        # Test the lookupclass migration
        sm.utilities.LookupClass = None
        # Test it twice
        for i in range(2):
            enableZope3Site(self.portal)
            self.assertEqual(sm.utilities.LookupClass, FiveVerifyingAdapterLookup)
            self.assertEqual(sm.utilities.__parent__, sm)
            self.assertEqual(sm.__parent__, self.portal)

    def testUpdateFTII18NDomain(self):
        doc = self.types.Document
        doc.i18n_domain = ''
        # Test it twice
        for i in range(2):
            updateFTII18NDomain(self.portal)
            self.assertEqual(doc.i18n_domain, 'plone')

    def testUpdateFTII18NDomainNonAscii(self):
        doc = self.types.Document
        doc.i18n_domain = ''
        doc.title = 'Foo\xc3'
        # Update FTI's
        updateFTII18NDomain(self.portal)
        # domain should have been updated
        self.assertEqual(doc.i18n_domain, '')

    def testAddDefaultAndForbiddenContentTypesProperties(self):
        # Should add the forbidden_contenttypes and default_contenttype property
        self.removeSiteProperty('forbidden_contenttypes')
        self.removeSiteProperty('default_contenttype')
        self.assertFalse(self.properties.site_properties.hasProperty('forbidden_contenttypes'))
        self.assertFalse(self.properties.site_properties.hasProperty('default_contenttype'))
        # Test it twice
        for i in range(2):
            loadMigrationProfile(self.portal, self.profile, ('propertiestool', ))
            self.assertTrue(self.properties.site_properties.hasProperty('forbidden_contenttypes'))
            self.assertTrue(self.properties.site_properties.hasProperty('default_contenttype'))
            self.assertEqual(self.properties.site_properties.forbidden_contenttypes,
                ('text/structured', 'text/restructured', 'text/x-rst',
                'text/plain', 'text/plain-pre', 'text/x-python',
                'text/x-web-markdown', 'text/x-web-intelligent', 'text/x-web-textile')
            )

    def testTablelessRemoval(self):
        st = getToolByName(self.portal, "portal_skins")
        if "Plone Tableless" not in st.getSkinSelections():
            st.addSkinSelection('Plone Tableless', 'one,two', make_default=True)
        # Test it twice
        for i in range(2):
            removeTablelessSkin(self.portal)
            self.assertFalse('Plone Tableless' in st.getSkinSelections())
            self.assertFalse(st.default_skin == 'Plone Tableless')

    def testLegacyPortletsConverted(self):
        self.setRoles(('Manager',))
        leftColumn = getUtility(IPortletManager, name=u'plone.leftcolumn', context=self.portal)
        rightColumn = getUtility(IPortletManager, name=u'plone.rightcolumn', context=self.portal)

        left = getMultiAdapter((self.portal, leftColumn,), IPortletAssignmentMapping, context=self.portal)
        right = getMultiAdapter((self.portal, rightColumn,), IPortletAssignmentMapping, context=self.portal)

        for k in left:
            del left[k]
        for k in right:
            del right[k]

        self.portal.left_slots = ['here/portlet_recent/macros/portlet',
                                  'here/portlet_news/macros/portlet',
                                  'here/portlet_related/macros/portlet']
        self.portal.right_slots = ['here/portlet_login/macros/portlet',
                                   'here/portlet_languages/macros/portlet']

        self.portal.Members.right_slots = []

        # Test it twice
        for i in range(2):
            convertLegacyPortlets(self.portal)

            self.assertEqual(self.portal.left_slots, [])
            self.assertEqual(self.portal.right_slots, [])

            left = getMultiAdapter((self.portal, leftColumn,), IPortletAssignmentMapping, context=self.portal)
            right = getMultiAdapter((self.portal, rightColumn,), IPortletAssignmentMapping, context=self.portal)

            lp = left.values()
            self.assertEqual(2, len(lp))

            self.assertTrue(isinstance(lp[0], portlets.recent.Assignment))
            self.assertTrue(isinstance(lp[1], portlets.news.Assignment))

            rp = right.values()
            self.assertEqual(1, len(rp))
            self.assertTrue(isinstance(rp[0], portlets.login.Assignment))

            members = self.portal.Members
            portletAssignments = getMultiAdapter((members, rightColumn,), ILocalPortletAssignmentManager)
            self.assertEqual(True, portletAssignments.getBlacklistStatus(CONTEXT_PORTLETS))

    def testLegacyPortletsConvertedNoSlots(self):
        self.setRoles(('Manager',))
        leftColumn = getUtility(IPortletManager, name=u'plone.leftcolumn', context=self.portal)
        rightColumn = getUtility(IPortletManager, name=u'plone.rightcolumn', context=self.portal)

        left = getMultiAdapter((self.portal, leftColumn,), IPortletAssignmentMapping, context=self.portal)
        right = getMultiAdapter((self.portal, rightColumn,), IPortletAssignmentMapping, context=self.portal)

        for k in left:
            del left[k]
        for k in right:
            del right[k]

        self.portal.left_slots = ['here/portlet_recent/macros/portlet',
                                  'here/portlet_news/macros/portlet']

        self.portal.Members.right_slots = []

        if hasattr(self.portal.aq_base, 'right_slots'):
            delattr(self.portal, 'right_slots')

        convertLegacyPortlets(self.portal)

        self.assertEqual(self.portal.left_slots, [])

        left = getMultiAdapter((self.portal, leftColumn,), IPortletAssignmentMapping, context=self.portal)
        right = getMultiAdapter((self.portal, rightColumn,), IPortletAssignmentMapping, context=self.portal)

        lp = left.values()
        self.assertEqual(2, len(lp))

        self.assertTrue(isinstance(lp[0], portlets.recent.Assignment))
        self.assertTrue(isinstance(lp[1], portlets.news.Assignment))

        rp = right.values()
        self.assertEqual(0, len(rp))

        members = self.portal.Members
        portletAssignments = getMultiAdapter((members, rightColumn,), ILocalPortletAssignmentManager)
        self.assertEqual(True, portletAssignments.getBlacklistStatus(CONTEXT_PORTLETS))

    def testLegacyPortletsConvertedBadSlots(self):
        self.setRoles(('Manager',))
        leftColumn = getUtility(IPortletManager, name=u'plone.leftcolumn', context=self.portal)
        rightColumn = getUtility(IPortletManager, name=u'plone.rightcolumn', context=self.portal)

        left = getMultiAdapter((self.portal, leftColumn,), IPortletAssignmentMapping, context=self.portal)
        right = getMultiAdapter((self.portal, rightColumn,), IPortletAssignmentMapping, context=self.portal)

        for k in left:
            del left[k]
        for k in right:
            del right[k]

        self.portal.left_slots = ['here/portlet_recent/macros/portlet',
                                  'here/portlet_news/macros/portlet',
                                  'foobar',]
        self.portal.right_slots = ['here/portlet_login/macros/portlet']

        self.portal.Members.right_slots = []

        convertLegacyPortlets(self.portal)
        left = getMultiAdapter((self.portal, leftColumn,), IPortletAssignmentMapping, context=self.portal)
        right = getMultiAdapter((self.portal, rightColumn,), IPortletAssignmentMapping, context=self.portal)

        self.assertEqual(self.portal.left_slots, [])
        self.assertEqual(self.portal.right_slots, [])

        lp = left.values()
        self.assertEqual(2, len(lp))

        self.assertTrue(isinstance(lp[0], portlets.recent.Assignment))
        self.assertTrue(isinstance(lp[1], portlets.news.Assignment))

        rp = right.values()
        self.assertEqual(1, len(rp))
        self.assertTrue(isinstance(rp[0], portlets.login.Assignment))

        members = self.portal.Members
        portletAssignments = getMultiAdapter((members, rightColumn,), ILocalPortletAssignmentManager)
        self.assertEqual(True, portletAssignments.getBlacklistStatus(CONTEXT_PORTLETS))

    def testLegacyPortletsConvertedNoMembersFolder(self):
        self.setRoles(('Manager',))
        leftColumn = getUtility(IPortletManager, name=u'plone.leftcolumn', context=self.portal)
        rightColumn = getUtility(IPortletManager, name=u'plone.rightcolumn', context=self.portal)

        left = getMultiAdapter((self.portal, leftColumn,), IPortletAssignmentMapping, context=self.portal)
        right = getMultiAdapter((self.portal, rightColumn,), IPortletAssignmentMapping, context=self.portal)

        for k in left:
            del left[k]
        for k in right:
            del right[k]

        self.portal.left_slots = ['here/portlet_recent/macros/portlet',
                                  'here/portlet_news/macros/portlet',
                                  'foobar',]
        self.portal.right_slots = ['here/portlet_login/macros/portlet']

        self.portal._delObject('Members')

        convertLegacyPortlets(self.portal)
        left = getMultiAdapter((self.portal, leftColumn,), IPortletAssignmentMapping, context=self.portal)
        right = getMultiAdapter((self.portal, rightColumn,), IPortletAssignmentMapping, context=self.portal)

        self.assertEqual(self.portal.left_slots, [])
        self.assertEqual(self.portal.right_slots, [])

        lp = left.values()
        self.assertEqual(2, len(lp))

        self.assertTrue(isinstance(lp[0], portlets.recent.Assignment))
        self.assertTrue(isinstance(lp[1], portlets.news.Assignment))

        rp = right.values()
        self.assertEqual(1, len(rp))
        self.assertTrue(isinstance(rp[0], portlets.login.Assignment))

    def testRegisterToolsAsUtilities(self):
        sm = getSiteManager(self.portal)
        interfaces = (ISiteRoot, IPloneSiteRoot,
                      IActionIconsTool, ISyndicationTool,
                      IMetadataTool, IPropertiesTool, IMailHost,
                      IUniqueIdAnnotationManagement, IUniqueIdGenerator,
                      IDiffTool, IMimetypesRegistryTool,
                      IPortalTransformsTool, IDiscussionTool, )
        if HAS_ATCT:
            interfaces += (IATCTTool,)
        for i in interfaces:
            sm.unregisterUtility(provided=i)
        registerToolsAsUtilities(self.portal)
        for i in interfaces:
            self.assertFalse(sm.queryUtility(i) is None)

        for i in interfaces:
            sm.unregisterUtility(provided=i)
        registerToolsAsUtilities(self.portal)
        registerToolsAsUtilities(self.portal)
        for i in interfaces:
            self.assertFalse(sm.queryUtility(i) is None)

    def testDontRegisterToolsAsUtilities(self):
        sm = getSiteManager(self.portal)
        interfaces = (ILanguageTool, IArchivistTool, IPortalModifierTool,
                      IPurgePolicyTool, IRepositoryTool, IStorageTool,
                      IFormControllerTool, IReferenceCatalog, IUIDCatalog,
                      ICalendarTool, IActionsTool, ICatalogTool,
                      IContentTypeRegistry, ISkinsTool, ITypesTool, IURLTool,
                      IConfigurableWorkflowTool, IPloneTool, ICSSRegistry,
                      IJSRegistry, IUniqueIdHandler, IFactoryTool,
                      IMembershipTool, IGroupTool, IGroupDataTool,
                      IMemberDataTool, IArchetypeTool, ICachingPolicyManager,
                      IRegistrationTool, ITranslationServiceTool,
                      ISetupTool, IQuickInstallerTool,
                     )
        for i in interfaces:
            sm.unregisterUtility(provided=i)
        registerToolsAsUtilities(self.portal)
        for i in interfaces:
            self.assertTrue(sm.queryUtility(i) is None)

        for i in interfaces:
            sm.unregisterUtility(provided=i)
        registerToolsAsUtilities(self.portal)
        registerToolsAsUtilities(self.portal)
        for i in interfaces:
            self.assertTrue(sm.queryUtility(i) is None)

    def testToolRegistration(self):
        for (tool_id, interface) in registration:
            self.assertEqual(getToolInterface(tool_id), interface)


class TestMigrations_v3_0_alpha1(MigrationTest):

    def afterSetUp(self):
        self.profile = 'profile-plone.app.upgrade.v30:3.0a1-3.0a2'
        self.actions = self.portal.portal_actions

    def testInstallRedirectorUtility(self):
        sm = getSiteManager(self.portal)
        sm.unregisterUtility(provided=IRedirectionStorage)
        # Test it twice
        for i in range(2):
            loadMigrationProfile(self.portal, self.profile, ('componentregistry', ))
            self.assertFalse(sm.queryUtility(IRedirectionStorage) is None)

    def testAddReaderEditorRoles(self):
        self.portal._delRoles(['Reader', 'Editor'])
        # Test it twice
        for i in range(2):
            addReaderAndEditorRoles(self.portal)
            self.assertTrue('Reader' in self.portal.valid_roles())
            self.assertTrue('Editor' in self.portal.valid_roles())
            self.assertTrue('Reader' in self.portal.acl_users.portal_role_manager.listRoleIds())
            self.assertTrue('Editor' in self.portal.acl_users.portal_role_manager.listRoleIds())
            self.assertTrue('View' in [r['name'] for r in self.portal.permissionsOfRole('Reader') if r['selected']])
            self.assertTrue('Modify portal content' in [r['name'] for r in self.portal.permissionsOfRole('Editor') if r['selected']])

    def testAddReaderEditorRolesPermissionOnly(self):
        self.portal.manage_permission('View', [], True)
        self.portal.manage_permission('Modify portal content', [], True)
        # Test it twice
        for i in range(2):
            addReaderAndEditorRoles(self.portal)
            self.assertTrue('Reader' in self.portal.valid_roles())
            self.assertTrue('Editor' in self.portal.valid_roles())
            self.assertTrue('Reader' in self.portal.acl_users.portal_role_manager.listRoleIds())
            self.assertTrue('Editor' in self.portal.acl_users.portal_role_manager.listRoleIds())
            self.assertTrue('View' in [r['name'] for r in self.portal.permissionsOfRole('Reader') if r['selected']])
            self.assertTrue('Modify portal content' in [r['name'] for r in self.portal.permissionsOfRole('Editor') if r['selected']])

    def testMigrateLocalroleForm(self):
        fti = self.portal.portal_types['Document']
        aliases = fti.getMethodAliases()
        aliases['sharing'] = 'folder_localrole_form'
        fti.setMethodAliases(aliases)
        fti.addAction('test', 'Test', 'string:${object_url}/folder_localrole_form', None, 'View', 'object')
        # Test it twice
        for i in range(2):
            migrateLocalroleForm(self.portal)
            self.assertEqual('@@sharing', fti.getMethodAliases()['sharing'])
            test_action = fti.listActions()[-1]
            self.assertEqual('string:${object_url}/@@sharing', test_action.getActionExpression())

    def testReorderUserActions(self):
        self.actions.user.moveObjectsToTop(['logout', 'undo', 'join'])
        # Test it twice
        for i in range(2):
            reorderUserActions(self.portal)
            # build a dict that has the position as the value to make it easier
            # to compare postions in the ordered list of actions
            n = 0
            sort = {}
            for action in self.actions.user.objectIds():
                sort[action] = n
                n += 1
            self.assertTrue(sort['preferences'] < sort['undo'])
            self.assertTrue(sort['undo'] < sort['logout'])
            self.assertTrue(sort['login'] < sort['join'])

    def testReorderUserActionsIncompleteActions(self):
        self.actions.user.moveObjectsToTop(['logout', 'undo', 'join'])
        self.actions.user._delObject('preferences')
        # Test it twice
        for i in range(2):
            reorderUserActions(self.portal)
            n = 0
            sort = {}
            for action in self.actions.user.objectIds():
                sort[action] = n
                n += 1
            self.assertTrue(sort['undo'] < sort['logout'])
            self.assertTrue(sort['login'] < sort['join'])


class TestMigrations_v3_0_alpha2(MigrationTest):

    def afterSetUp(self):
        self.profile = 'profile-plone.app.upgrade.v30:3.0a2-3.0b1'
        self.actions = self.portal.portal_actions
        self.properties = self.portal.portal_properties
        self.cp = self.portal.portal_controlpanel

    def testAddVariousProperties(self):
        PROPERTIES = ('enable_link_integrity_checks', 'enable_sitemap',
                      'external_links_open_new_window', 'many_groups',
                      'number_of_days_to_keep', 'webstats_js')
        for prop in PROPERTIES:
            self.removeSiteProperty(prop)
        sheet = self.properties.site_properties
        # Test it twice
        for i in range(2):
            loadMigrationProfile(self.portal, self.profile, ('propertiestool', ))
            for prop in PROPERTIES:
                self.assertTrue(sheet.hasProperty(prop))

    def testInstallContentrulesAndLanguageUtilities(self):
        sm = getSiteManager()
        INTERFACES = (IRuleStorage, ICountries, IContentLanguages,
                      IMetadataLanguages)
        for i in INTERFACES:
            sm.unregisterUtility(provided=i)
        # Test it twice
        for i in range(2):
            loadMigrationProfile(self.portal, self.profile, ('componentregistry', ))
            for i in INTERFACES:
                self.assertFalse(sm.queryUtility(i) is None)

    def testAddEmailCharsetProperty(self):
        if self.portal.hasProperty('email_charset'):
            self.portal.manage_delProperties(['email_charset'])
        # Test it twice
        for i in range(2):
            loadMigrationProfile(self.portal, self.profile, ('properties', ))
            self.assertTrue(self.portal.hasProperty('email_charset'))
            self.assertEqual(self.portal.getProperty('email_charset'), 'utf-8')

    def testUpdateMemberSecurity(self):
        # These properties were removed in Plone 5, so we add them
        # manually here if needed and check if they are properly updated by the
        # updateMemberSecurity upgrade step
        pprop = getToolByName(self.portal, 'portal_properties')
        try:
            self.portal.manage_addProperty('validate_email', False, 'boolean')
        except BadRequest:  # property is already there
            pass
        try:
            pprop.site_properties.manage_addProperty(
                'allowAnonymousViewAbout', True, 'boolean')
        except BadRequest:  # property is already there
            pass

        updateMemberSecurity(self.portal)

        self.assertEqual(
            pprop.site_properties.getProperty('allowAnonymousViewAbout'),
            False
        )

        pmembership = getToolByName(self.portal, 'portal_membership')
        self.assertEqual(pmembership.memberareaCreationFlag, False)
        self.assertEqual(self.portal.getProperty('validate_email'), True)

        app_roles = self.portal.rolesOfPermission(permission='Add portal member')
        app_perms = self.portal.permission_settings(permission='Add portal member')
        acquire_check = app_perms[0]['acquire']
        reg_roles = []
        for appperm in app_roles:
            if appperm['selected'] == 'SELECTED':
                reg_roles.append(appperm['name'])
        self.assertTrue('Manager' in reg_roles)
        self.assertTrue('Owner' in reg_roles)
        self.assertEqual(acquire_check, '')

    def testPASPluginInterfaces(self):
        pas = self.portal.acl_users
        from Products.PluggableAuthService.interfaces.plugins import IUserEnumerationPlugin
        pas.plugins.deactivatePlugin(IUserEnumerationPlugin, 'mutable_properties')
        updatePASPlugins(self.portal)

        plugin = pas.mutable_properties
        for intf_id in plugin.listInterfaces():
            try:
                intf = pas.plugins._getInterfaceFromName(intf_id)
                self.assertTrue('mutable_properties' in pas.plugins.listPluginIds(intf))
            except KeyError:
                # Ignore unregistered interface types
                pass

    def testUpdateConfigletTitles(self):
        collection = self.cp.getActionObject('Plone/portal_atct')
        language = self.cp.getActionObject('Plone/PloneLanguageTool')
        navigation = self.cp.getActionObject('Plone/NavigationSettings')
        types = self.cp.getActionObject('Plone/TypesSettings')
        users = self.cp.getActionObject('Plone/UsersGroups')
        users2 = self.cp.getActionObject('Plone/UsersGroups2')
        # test it twice
        for i in range(2):
            updateConfigletTitles(self.portal)
            self.assertEqual(collection.title, 'Collection')
            self.assertEqual(language.title, 'Language')
            self.assertEqual(navigation.title, 'Navigation')
            self.assertEqual(types.title, 'Types')
            self.assertEqual(users.title, 'Users and Groups')
            self.assertEqual(users2.title, 'Users and Groups')

    def testAddCacheForResourceRegistry(self):
        ram_cache_id = 'ResourceRegistryCache'
        # first remove the cache manager and make sure it's removed
        self.portal._delObject(ram_cache_id)
        self.assertFalse(ram_cache_id in self.portal.objectIds())
        cssreg = self.portal.portal_css
        cssreg.ZCacheable_setEnabled(0)
        cssreg.ZCacheable_setManagerId(None)
        self.assertFalse(cssreg.ZCacheable_enabled())
        self.assertTrue(cssreg.ZCacheable_getManagerId() is None)
        jsreg = self.portal.portal_javascripts
        jsreg.ZCacheable_setEnabled(0)
        jsreg.ZCacheable_setManagerId(None)
        self.assertFalse(jsreg.ZCacheable_enabled())
        self.assertTrue(jsreg.ZCacheable_getManagerId() is None)
        # Test it twice
        for i in range(2):
            addCacheForResourceRegistry(self.portal)
            self.assertTrue(ram_cache_id in self.portal.objectIds())
            self.assertTrue(cssreg.ZCacheable_enabled())
            self.assertFalse(cssreg.ZCacheable_getManagerId() is None)
            self.assertTrue(jsreg.ZCacheable_enabled())
            self.assertFalse(jsreg.ZCacheable_getManagerId() is None)

    def testObjectProvidesIndex(self):
        catalog = getToolByName(self.portal, 'portal_catalog')
        if 'object_provides' in catalog.indexes():
            catalog.delIndex('object_provides')
        self.assertFalse('object_provides' in catalog.indexes())
        # Test it twice
        for i in range(2):
            addObjectProvidesIndex(self.portal)
            self.assertTrue('object_provides' in catalog.indexes())

    def testMigratePloneTool(self):
        tool = self.portal.plone_utils
        tool.meta_type = 'PlonePAS Utilities Tool'
        # Test it twice
        for i in range(2):
            restorePloneTool(self.portal)
            tool = self.portal.plone_utils
            self.assertEqual('Plone Utility Tool', tool.meta_type)

    def testInstallPloneLanguageTool(self):
        super(self.portal.__class__, self.portal).manage_delObjects(
            ['portal_languages'])
        self.uninstallProduct('PloneLanguageTool')
        qi = getToolByName(self.portal, "portal_quickinstaller")
        # Test it twice
        for i in range(2):
            installProduct('PloneLanguageTool', self.portal)
            self.assertTrue(qi.isProductInstalled('PloneLanguageTool'))
            self.assertTrue('portal_languages' in self.portal.keys())


class TestMigrations_v3_0(MigrationTest):

    def afterSetUp(self):
        self.profile = 'profile-plone.app.upgrade.v30:3.0b1-3.0b2'
        self.actions = self.portal.portal_actions
        self.skins = self.portal.portal_skins
        self.types = self.portal.portal_types
        self.workflow = self.portal.portal_workflow
        self.properties = getToolByName(self.portal, 'portal_properties')

    def testAddContentRulesAction(self):
        self.portal.portal_actions.object._delObject('contentrules')
        # Test it twice
        for i in range(2):
            loadMigrationProfile(self.portal, self.profile, ('actions', ))
            self.assertTrue('contentrules' in self.portal.portal_actions.object.objectIds())

    def testChangeOrderOfActionProviders(self):
        self.actions.deleteActionProvider('portal_types')
        self.actions.addActionProvider('portal_types')
        self.assertEqual(
            self.actions.listActionProviders(),
            ('portal_workflow', 'portal_actions', 'portal_types'))
        # Test it twice
        for i in range(2):
            changeOrderOfActionProviders(self.portal)
            self.assertEqual(
                self.actions.listActionProviders(),
                ('portal_workflow', 'portal_types', 'portal_actions'))

    def testCleanupOldActions(self):
        reply = Action('reply', title='Reply')
        logged_in = Action('logged_in', title='Logged in')
        change_ownership = Action('change_ownership', title='Change ownership')

        object_ = self.actions.object
        object_tabs = getattr(self.actions, 'object_tabs', None)
        if object_tabs is None:
            category = 'object_tabs'
            self.actions._setObject(category, ActionCategory(id=category))
            object_tabs = self.actions.object_tabs
        if getattr(self.actions, 'global', None) is None:
            category = 'global'
            self.actions._setObject(category, ActionCategory(id=category))

        if not 'reply' in object_.keys():
            object_._setObject('reply', reply)
        user = self.actions.user
        if not 'logged_in' in user.keys():
            user._setObject('logged_in', logged_in)
        if not 'change_ownership' in object_tabs.keys():
            object_tabs._setObject('change_ownership', change_ownership)
        del object_tabs

        # Test it twice
        for i in range(2):
            cleanupOldActions(self.portal)
            self.assertFalse('reply' in object_.keys())
            self.assertFalse('logged_in' in user.keys())
            self.assertFalse('object_tabs' in self.actions.keys())
            self.assertFalse('global' in self.actions.keys())

    def testCharsetCleanup(self):
        if not self.portal.hasProperty('default_charset'):
            self.portal.manage_addProperty('default_charset', '', 'string')
        # Test it twice
        for i in range(2):
            self.portal.manage_changeProperties(default_charset = 'latin1')
            cleanDefaultCharset(self.portal)
            self.assertEqual(self.portal.getProperty('default_charset', 'nothere'),
                    'latin1')
        # Test it twice
        for i in range(2):
            self.portal.manage_changeProperties(default_charset = '')
            cleanDefaultCharset(self.portal)
            self.assertEqual(self.portal.getProperty('default_charset', 'nothere'),
                    'nothere')

    def testAutoGroupCreated(self):
        pas = self.portal.acl_users
        ids = pas.objectIds(['Automatic Group Plugin'])
        if ids:
            pas.manage_delObjects(ids)
        addAutoGroupToPAS(self.portal)
        self.assertEqual(pas.objectIds(['Automatic Group Plugin']),
                ['auto_group'])
        plugin = pas.auto_group
        interfaces = [info['interface'] for info in pas.plugins.listPluginTypeInfo()]
        for iface in interfaces:
            if plugin.testImplements(iface):
                self.assertFalse('auto_group' not in pas.plugins.listPluginIds(iface))
        self.assertEqual(len(pas.searchGroups(id='AuthenticatedUsers',
                                              exact_match=True)), 1)

    def testPloneS5(self):
        pt = getToolByName(self.portal, "portal_types")
        document = pt.restrictedTraverse('Document')
        document.addAction('s5_presentation',
            name='View as presentation',
            action="string:${object/absolute_url}/document_s5_presentation",
            condition='python:object.document_s5_alter(test=True)',
            permission='View',
            category='document_actions',
            visible=1,
            )
        action_ids = [x.getId() for x in document.listActions()]
        self.assertTrue("s5_presentation" in action_ids)
        # Test it twice
        for i in range(2):
            removeS5Actions(self.portal)
            action_ids = [x.getId() for x in document.listActions()]
            self.assertFalse("s5_presentation" in action_ids)

    def testAddContributorToCreationPermissions(self):
        self.portal._delRoles(['Contributor',])
        for p in ['Add portal content', 'Add portal folders', 'ATContentTypes: Add Document',
                    'ATContentTypes: Add Event',
                    'ATContentTypes: Add File', 'ATContentTypes: Add Folder',
                    'ATContentTypes: Add Image', 'ATContentTypes: Add Link',
                    'ATContentTypes: Add News Item', ]:
            self.portal.manage_permission(p, ['Manager', 'Owner'], True)
        # Test it twice
        for i in range(2):
            addContributorToCreationPermissions(self.portal)
            self.assertTrue('Contributor' in self.portal.valid_roles())
            self.assertTrue('Contributor' in self.portal.acl_users.portal_role_manager.listRoleIds())
            for p in ['Add portal content', 'Add portal folders', 'ATContentTypes: Add Document',
                        'ATContentTypes: Add Event',
                        'ATContentTypes: Add File', 'ATContentTypes: Add Folder',
                        'ATContentTypes: Add Image', 'ATContentTypes: Add Link',
                        'ATContentTypes: Add News Item', ]:
                self.assertTrue(p in [r['name'] for r in
                                    self.portal.permissionsOfRole('Contributor') if r['selected']])

    def testAddContributerToCreationPermissionsNoStomp(self):
        self.portal.manage_permission('Add portal content', ['Manager'], False)
        # Test it twice
        for i in range(2):
            addContributorToCreationPermissions(self.portal)
            roles = sorted([r['name'] for r in self.portal.rolesOfPermission('Add portal content') if r['selected']])
            self.assertEqual(['Contributor', 'Manager'], roles)
            self.assertEqual(False, bool(self.portal.acquiredRolesAreUsedBy('Add portal content')))

    def testAddBeta2VersioningPermissionsToNewRoles(self):
        # This upgrade just uses GS to apply the role changes,
        # these permissions will not have been installed previously,
        # so this should be safe
        for p in ['CMFEditions: Apply version control',
                  'CMFEditions: Save new version',
                  'CMFEditions: Access previous versions',
                  'CMFEditions: Revert to previous versions',
                  'CMFEditions: Checkout to location']:
            self.portal.manage_permission(p, ['Manager', 'Owner'], True)
        # Test it twice
        for i in range(2):
            loadMigrationProfile(self.portal,
                    'profile-plone.app.upgrade.v30:3.0b1-3.0b2',
                    steps=["rolemap"])
            for p in ['CMFEditions: Apply version control',
                      'CMFEditions: Save new version',
                      'CMFEditions: Access previous versions']:
                self.assertTrue(p in [r['name'] for r in
                                    self.portal.permissionsOfRole('Contributor') if r['selected']])
                self.assertTrue(p in [r['name'] for r in
                                    self.portal.permissionsOfRole('Editor') if r['selected']])
            for p in ['CMFEditions: Revert to previous versions',
                      'CMFEditions: Checkout to location']:
                self.assertTrue(p in [r['name'] for r in
                                    self.portal.permissionsOfRole('Editor') if r['selected']])

    def testRemoveSharingAction(self):
        fti = self.types['Document']
        fti.addAction(id='local_roles', name='Sharing',
                      action='string:${object_url}/sharing',
                      condition=None, permission='Manage properties',
                      category='object')
        # Test it twice
        for i in range(2):
            removeSharingAction(self.portal)
            self.assertFalse('local_roles' in [a.id for a in fti.listActions()])

    def testAddEditorToCreationPermissions(self):
        for p in ['Manage properties', 'Modify view template', 'Request review']:
            self.portal.manage_permission(p, ['Manager', 'Owner'], True)
        # Test it twice
        for i in range(2):
            addEditorToSecondaryEditorPermissions(self.portal)
            for p in ['Manage properties', 'Modify view template', 'Request review']:
                self.assertTrue(p in [r['name'] for r in
                    self.portal.permissionsOfRole('Editor') if r['selected']])

    def testAddEditorToCreationPermissionsNoStomp(self):
        self.portal.manage_permission('Manage properties', ['Manager'], False)
        # Test it twice
        for i in range(2):
            addEditorToSecondaryEditorPermissions(self.portal)
            roles = sorted([r['name'] for r in self.portal.rolesOfPermission('Manage properties') if r['selected']])
            self.assertEqual(['Editor', 'Manager'], roles)
            self.assertEqual(False, bool(self.portal.acquiredRolesAreUsedBy('Manage properties')))

    def testUpdateEditActionConditionForLocking(self):
        lockable_types = ['Document', 'Event', 'File', 'Folder',
                          'Image', 'Link', 'News Item', 'Topic']
        for contentType in lockable_types:
            fti = self.types.getTypeInfo(contentType)
            for action in fti.listActions():
                if action.getId() == 'edit':
                    action.condition = ''
        # Test it twice
        for i in range(2):
            updateEditActionConditionForLocking(self.portal)
            for contentType in lockable_types:
                fti = self.types.getTypeInfo(contentType)
                for action in fti.listActions():
                    if action.getId() == 'edit':
                        self.assertEqual(action.condition.text,
                            "not:object/@@plone_lock_info/is_locked_for_current_user|python:True")

    def testUpdateEditExistingActionConditionForLocking(self):
        fti = self.types.getTypeInfo('Document')
        for action in fti.listActions():
            if action.getId() == 'edit':
                action.condition = Expression("foo")
        # Test it twice
        for i in range(2):
            updateEditActionConditionForLocking(self.portal)
            fti = self.types.getTypeInfo('Document')
            for action in fti.listActions():
                if action.getId() == 'edit':
                    self.assertEqual(action.condition.text, 'foo')

    def testAddOnFormUnloadRegistrationJS(self):
        jsreg = self.portal.portal_javascripts
        # unregister first
        jsreg.unregisterResource('unlockOnFormUnload.js')
        script_ids = jsreg.getResourceIds()
        self.assertFalse('unlockOnFormUnload.js' in script_ids)
        # Test it twice
        for i in range(2):
            addOnFormUnloadJS(self.portal)
            script_ids = jsreg.getResourceIds()
            self.assertTrue('unlockOnFormUnload.js' in script_ids)

    def testUpdateTopicTitle(self):
        topic = self.types.get('Topic')
        topic.title = 'Old'
        # Test it twice
        for i in range(2):
            updateTopicTitle(self.portal)
            self.assertEqual(topic.title, 'Collection')

    def testAddIntelligentText(self):
        # Before the upgrade, the mime type and transforms of intelligent text
        # are not available. They *are* here in a fresh site, so we may need
        # to remove them first for testing. First we remove the transforms,
        # as they depend on the mimetype being there.
        missing_transforms = ["web_intelligent_plain_text_to_html",
                              "html_to_web_intelligent_plain_text"]
        ptr = self.portal.portal_transforms
        current_transforms = ptr.objectIds()
        for trans in missing_transforms:
            if trans in current_transforms:
                ptr.unregisterTransform(trans)
        # Then we remove the mime type
        mime_type = 'text/x-web-intelligent'
        mtr = self.portal.mimetypes_registry
        current_types = mtr.list_mimetypes()
        if mime_type in current_types:
            mtr.manage_delObjects((mime_type,))
        # now all are gone:
        self.assertFalse(mime_type in mtr.list_mimetypes())
        self.assertFalse(set(ptr.objectIds()).issuperset(set(missing_transforms)))
        # Test it twice
        for i in range(2):
            addIntelligentText(self.portal)
            # now all are back:
            self.assertTrue(mime_type in mtr.list_mimetypes())
            self.assertTrue(set(ptr.objectIds()).issuperset(set(missing_transforms)))

    def testInstallNewModifiers(self):
        # ensure the new modifiers are installed
        modifiers = self.portal.portal_modifier
        self.assertTrue('AbortVersioningOfLargeFilesAndImages' in
                                                          modifiers.objectIds())
        modifiers.manage_delObjects(['AbortVersioningOfLargeFilesAndImages',
                                     'SkipVersioningOfLargeFilesAndImages'])
        self.assertFalse('AbortVersioningOfLargeFilesAndImages' in
                                                          modifiers.objectIds())
        installNewModifiers(self.portal)
        self.assertTrue('AbortVersioningOfLargeFilesAndImages' in
                                                          modifiers.objectIds())
        self.assertTrue('SkipVersioningOfLargeFilesAndImages' in
                                                          modifiers.objectIds())

    def testInstallNewModifiersTwice(self):
        # ensure that we get no errors when run twice
        installNewModifiers(self.portal)
        installNewModifiers(self.portal)

    def testInstallNewModifiersDoesNotStompChanges(self):
        # ensure that reinstalling doesn't kill customizations
        modifiers = self.portal.portal_modifier
        modifiers.AbortVersioningOfLargeFilesAndImages.max_size = 1000
        installNewModifiers(self.portal)
        self.assertEqual(modifiers.AbortVersioningOfLargeFilesAndImages.max_size,
                         1000)

    def testInstallNewModifiersNoTool(self):
        # make sure there are no errors if the tool is missing
        self.portal._delObject('portal_modifier')
        installNewModifiers(self.portal)


class TestFunctionalMigrations(FunctionalUpgradeTestCase):

    def testBaseUpgrade(self):
        self.importFile(__file__, 'test-base.zexp')
        oldsite, result = self.migrate()

        mig = oldsite.portal_migration
        self.assertFalse(mig.needUpgrading())

    def testFullUpgrade(self):
        self.importFile(__file__, 'test-full.zexp')
        oldsite, result = self.migrate()

        mig = oldsite.portal_migration
        self.assertFalse(mig.needUpgrading())


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    if not version_match('3.0'):
        return suite
    suite.addTest(makeSuite(TestMigrations_v2_5_x))
    suite.addTest(makeSuite(TestMigrations_v3_0_Actions))
    suite.addTest(makeSuite(TestMigrations_v3_0_alpha1))
    suite.addTest(makeSuite(TestMigrations_v3_0_alpha2))
    suite.addTest(makeSuite(TestMigrations_v3_0))
    suite.addTest(makeSuite(TestFunctionalMigrations))
    return suite
