from zope.component import getUtility
from zope.component import getSiteManager
from zope.component import getMultiAdapter
from plone.portlets.interfaces import IPortletManager
from Products.CMFCore.utils import getToolByName
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.app.viewletmanager.interfaces import IViewletSettingsStorage

from plone.app.upgrade.tests.base import FunctionalUpgradeTestCase
from plone.app.upgrade.tests.base import MigrationTest

import alphas


class PASUpgradeTest(MigrationTest):

    def test_double_upgrade(self):
        # Check that calling our upgrade twice does no harm.
        alphas.lowercase_email_login(self.portal)
        alphas.lowercase_email_login(self.portal)

    def test_upgrade_with_email_login(self):
        pas = getToolByName(self.portal, 'acl_users')
        regtool = getToolByName(self.portal, 'portal_registration')
        regtool.addMember('JOE', 'somepassword')
        self.assertEqual(pas.getUserById('JOE').getUserName(), 'JOE')

        # First call.
        alphas.lowercase_email_login(self.portal)
        self.assertEqual(pas.getProperty('login_transform'), '')
        self.assertEqual(pas.getUserById('JOE').getUserName(), 'JOE')

        # If email as login is enabled, we want to use lowercase login
        # names, even when that login name is not an email address.
        ptool = getToolByName(self.portal, 'portal_properties')
        ptool.site_properties.manage_changeProperties(use_email_as_login=True)

        # Second call.
        alphas.lowercase_email_login(self.portal)
        self.assertEqual(pas.getProperty('login_transform'), 'lower')
        self.assertEqual(pas.getUserById('JOE').getUserName(), 'joe')

    def test_footer_portletmanager_added(self):
        sm = getSiteManager(self.portal)
        registrations = [r.name for r in sm.registeredUtilities()
                         if IPortletManager == r.provided]
        self.assertTrue('plone.footerportlets' in registrations)
        manager = getUtility(IPortletManager, name='plone.footerportlets', context=self.portal)
        mapping = getMultiAdapter((self.portal, manager), IPortletAssignmentMapping)
        self.assertEqual(['footer', 'actions', 'colophon'], mapping.keys())

    def test_footer_viewlets_hidden(self):

        storage = getUtility(IViewletSettingsStorage)
        manager = "plone.portalfooter"
        skinname = self.portal.getCurrentSkinName()

        hidden_viewlets = storage.getHidden(manager, skinname)

        self.assertEqual((u'plone.colophon', u'plone.site_actions'),
                         hidden_viewlets)

    def test_migrate_members_default_layout(self):
        members = self.portal['Members']
        from OFS.SimpleItem import SimpleItem
        members._setOb('index_html', SimpleItem())
        self.assertIsNotNone(members.get('index_html', None))
        
        from plone.app.upgrade.v50.alphas import migrate_members_default_view
        migrate_members_default_view(self.portal)

        self.assertIsNone(members.get('index_html', None))
        self.assertEqual(members.getLayout(), '@@member-search')


class TestFunctionalMigrations(FunctionalUpgradeTestCase):
    """Run an upgrade from a real Plone 4.0 ZEXP dump.

    Then test that various things are set up correctly.
    """

    def afterSetUp(self):
        super(TestFunctionalMigrations, self).afterSetUp()
        # test upgrade from Plone 4.0 zexp
        self.importFile(__file__, 'test-full.zexp')
        self.portal, result = self.migrate()

    def testFullyUpgraded(self):
        self.assertFalse(self.portal.portal_migration.needUpgrading())

    def testCanRenderHomepage(self):
        self.assertTrue('Welcome' in self.portal())

    def testBarcelonetaThemeIsInstalled(self):
        # skin is default
        self.assertEqual(self.portal.portal_skins.getDefaultSkin(), 'Plone Default')
        # diazo is enabled
        registry = self.portal.portal_registry
        self.assertTrue(registry['plone.app.theming.interfaces.IThemeSettings.enabled'])
        # rules are active
        self.assertEqual(
            registry['plone.app.theming.interfaces.IThemeSettings.rules'],
            '++theme++barceloneta/rules.xml',
            )


def test_suite():
    # Skip these tests on Plone 4
    from unittest import TestSuite, makeSuite
    try:
        from Products.CMFPlone.factory import _IMREALLYPLONE5
    except ImportError:
        return TestSuite()
    else:
        suite = TestSuite()
        suite.addTest(makeSuite(PASUpgradeTest))
        suite.addTest(makeSuite(TestFunctionalMigrations))
        return suite
