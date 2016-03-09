from Products.CMFCore.utils import getToolByName
from plone.app.upgrade.tests.base import MigrationTest
from plone.app.upgrade.v50.testing import REAL_UPGRADE_FUNCTIONAL
from plone.app.viewletmanager.interfaces import IViewletSettingsStorage
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import IPortletManager
from plone.registry.interfaces import IRegistry
from plone.testing.z2 import Browser
from zope.component import getMultiAdapter
from zope.component import getSiteManager
from zope.component import getUtility

import unittest

try:
    from Products.CMFPlone.factory import _IMREALLYPLONE5
    _IMREALLYPLONE5  # pyflakes
except ImportError:
    PLONE_5 = False
else:
    PLONE_5 = True

if PLONE_5:
    from plone.app.upgrade.v50 import alphas


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
        registry = getUtility(IRegistry)
        from Products.CMFPlone.interfaces import ISecuritySchema
        security_settings = registry.forInterface(ISecuritySchema,
                                                  prefix="plone")
        security_settings.use_email_as_login = True

        # Second call.
        alphas.lowercase_email_login(self.portal)
        self.assertEqual(pas.getProperty('login_transform'), 'lower')
        self.assertEqual(pas.getUserById('JOE').getUserName(), 'joe')

    def test_footer_portletmanager_added(self):
        sm = getSiteManager(self.portal)
        registrations = [r.name for r in sm.registeredUtilities()
                         if IPortletManager == r.provided]
        self.assertTrue('plone.footerportlets' in registrations)
        manager = getUtility(
            IPortletManager, name='plone.footerportlets', context=self.portal)
        mapping = getMultiAdapter(
            (self.portal, manager), IPortletAssignmentMapping)
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


class TestFunctionalMigrations(unittest.TestCase):
    """Run an upgrade from a real Plone 4.0 ZEXP dump.

    Then test that various things are set up correctly.
    """

    layer = REAL_UPGRADE_FUNCTIONAL

    def setUp(self):
        self.portal = self.layer['app'].test

    def testFullyUpgraded(self):
        self.assertFalse(self.portal.portal_migration.needUpgrading())

    def testCanRenderHomepage(self):
        browser = Browser(self.layer['app'])
        browser.open('http://nohost/test')
        self.assertTrue('Welcome' in browser.contents)

    def testBarcelonetaThemeIsInstalled(self):
        # skin is default
        self.assertEqual(
            self.portal.portal_skins.getDefaultSkin(), 'Plone Default')
        # diazo is enabled
        registry = self.portal.portal_registry
        self.assertTrue(
            registry['plone.app.theming.interfaces.IThemeSettings.enabled'])
        # rules are active
        self.assertEqual(
            registry['plone.app.theming.interfaces.IThemeSettings.rules'],
            '/++theme++barceloneta/rules.xml',
        )


def test_suite():
    # Skip these tests on Plone 4
    from unittest import TestSuite, makeSuite
    if not PLONE_5:
        return TestSuite()
    else:
        suite = TestSuite()
        suite.addTest(makeSuite(PASUpgradeTest))
        suite.addTest(makeSuite(TestFunctionalMigrations))
        return suite
