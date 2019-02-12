# -*- coding: utf-8 -*-
from pkg_resources import get_distribution
from pkg_resources import parse_version
from plone.app.upgrade.tests.base import MigrationTest
from plone.app.upgrade.v50.testing import REAL_UPGRADE_FUNCTIONAL
from plone.app.viewletmanager.interfaces import IViewletSettingsStorage
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import IPortletManager
from plone.registry.interfaces import IRegistry
from plone.testing.z2 import Browser
from Products.CMFCore.utils import getToolByName
from zope.component import getMultiAdapter
from zope.component import getSiteManager
from zope.component import getUtility
import six
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

plone_version = get_distribution('Products.CMFPlone').version
PLONE_52 = parse_version(plone_version) >= parse_version('5.2a1')


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
                                                  prefix='plone')
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
        manager = 'plone.portalfooter'
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


@unittest.skipIf(
    PLONE_52 or not PLONE_5, "Only test in Plone 5.0 and 5.1")
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


class VariousTest(MigrationTest):

    def test_fix_double_smaxage(self):
        from plone.registry.interfaces import IRegistry
        from plone.registry.record import Record
        from plone.registry import FieldRef
        from plone.app.upgrade.v50.final import fix_double_smaxage
        # Run the upgrade before plone.app.caching is installed,
        # to check that it does not harm.
        portal_setup = self.layer['portal'].portal_setup
        fix_double_smaxage(portal_setup)
        registry = getUtility(IRegistry)
        maxage = 'plone.app.caching.strongCaching.plone.resource.maxage'
        def_maxage = 'plone.app.caching.strongCaching.maxage'
        def_smaxage = 'plone.app.caching.strongCaching.smaxage'
        # Install default caching profile.
        portal_setup.runAllImportStepsFromProfile(
            'plone.app.caching:default',
        )
        self.assertTrue(def_maxage in registry)
        self.assertTrue(def_smaxage in registry)
        # Run upgrade.
        fix_double_smaxage(portal_setup)
        # Install the with-caching-proxy settings.
        portal_setup.runAllImportStepsFromProfile(
            'plone.app.caching:with-caching-proxy',
        )
        # Run upgrade.
        fix_double_smaxage(portal_setup)

        # Old situation had maxage referencing the s-maxage definition:
        field_ref = FieldRef(def_smaxage, registry.records[def_smaxage].field)
        registry.records[maxage] = Record(field_ref, 999)
        self.assertEqual(
            registry.records[maxage].field.recordName, def_smaxage)
        self.assertEqual(registry[maxage], 999)
        self.assertIn('shared', registry.records[maxage].field.title.lower())
        # Run upgrade.
        fix_double_smaxage(portal_setup)
        # Test that this fixes the reference and keeps the value.
        self.assertEqual(
            registry.records[maxage].field.recordName, def_maxage)
        self.assertEqual(registry[maxage], 999)
        self.assertNotIn(
            'shared', registry.records[maxage].field.title.lower())
        # Run upgrade.
        fix_double_smaxage(portal_setup)
        self.assertEqual(
            registry.records[maxage].field.recordName, def_maxage)
        self.assertEqual(registry[maxage], 999)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(PASUpgradeTest))
    suite.addTest(makeSuite(VariousTest))
    if not six.PY2 or not PLONE_5:
        return TestSuite()
    else:
        suite.addTest(makeSuite(TestFunctionalMigrations))
    return suite
