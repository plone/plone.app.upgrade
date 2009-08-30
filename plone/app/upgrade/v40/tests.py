from zope.component import getSiteManager, queryUtility
from zope.ramcache.interfaces.ram import IRAMCache

from Products.MailHost.interfaces import IMailHost
from Products.CMFCore.ActionInformation import Action
from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.tests.base import MigrationTest

from plone.app.upgrade.v40.alphas import _KNOWN_ACTION_ICONS
from plone.app.upgrade.v40.alphas import migrateActionIcons
from plone.app.upgrade.v40.alphas import addOrReplaceRamCache
from plone.app.upgrade.v40.alphas import migrateMailHost

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
        self.aitool = getToolByName(self.portal, 'portal_actionicons')
        self.cptool = getToolByName(self.portal, 'portal_controlpanel')

    def testProfile(self):
        # This tests the whole migration profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.failUnless(True)

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
        self.assertEqual(self.aitool.getActionIcon('object_buttons', 'test_id'),
                        'test.gif')
        # Test it twice
        for i in range(2):
            migrateActionIcons(self.portal)
            icons = [ic.getActionId() for ic in self.aitool.listActionIcons()]
            self.failIf('test_id' in icons)
            self.failIf('test2_id' in icons)
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
            icon_expr=''
            )

        action = self.cptool.getActionObject('Plone/test_id')
        self.assertEqual(action.getIconExpression(), '')
        self.assertEqual(self.aitool.getActionIcon('controlpanel', 'test_id'),
                         'test.gif')
        # Test it twice
        for i in range(2):
            migrateActionIcons(self.portal)
            icons = [ic.getActionId() for ic in self.aitool.listActionIcons()]
            self.failIf('test_id' in icons)
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
        self.assertEqual(tt.Document.icon_expr, "string:${portal_url}/document_icon.png")

    def testPngContentIcons(self):
        tt = getToolByName(self.portal, "portal_types")
        tt.Document.content_icon = "document_icon.gif"
        loadMigrationProfile(self.portal, self.profile, ('typeinfo', ))
        self.assertEqual(tt.Document.content_icon, "document_icon.png")

    def testAddRAMCache(self):
        # Test it twice
        for i in range(2):
            sm = getSiteManager()
            sm.unregisterUtility(provided=IRAMCache)
            util = queryUtility(IRAMCache)
            self.failUnless(util.maxAge == 86400)
            addOrReplaceRamCache(self.portal)
            util = queryUtility(IRAMCache)
            self.failUnless(util.maxAge == 3600)

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
            self.failUnless(util.maxAge == 3600)

    def testReplaceSecureMailHost(self):
        portal = self.portal
        sm = getSiteManager(context=portal)
        # try it with an unmodified site to ensure it doesn't give any errors
        migrateMailHost(portal)
        portal._delObject('MailHost')
        # Run it with our MailHost replaced
        portal._setObject('MailHost', FakeSecureMailHost())
        self.assertEqual(portal.MailHost.meta_type, 'Secure Mail Host')
        sm.unregisterUtility(provided=IMailHost)
        sm.registerUtility(portal.MailHost, provided=IMailHost)
        migrateMailHost(portal)
        new_mh = portal.MailHost
        self.failUnlessEqual(new_mh.meta_type, 'Mail Host')
        self.failUnlessEqual(new_mh.title, 'Fake MailHost')
        self.failUnlessEqual(new_mh.smtp_host, 'smtp.example.com')
        self.failUnlessEqual(new_mh.smtp_port, 587)
        self.failUnlessEqual(new_mh.smtp_uid, 'me')
        self.failUnlessEqual(new_mh.smtp_pwd, 'secret')
        #Force TLS is always false, because SMH has no equivalent option
        self.failUnlessEqual(new_mh.force_tls, False)

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestMigrations_v4_0alpha1))
    return suite
