# -*- coding: utf-8 -*-

from plone.app.upgrade.v52.testing import REAL_UPGRADE_FUNCTIONAL
from plone.testing.z2 import Browser
from pkg_resources import get_distribution

import unittest

PLONE_51 = get_distribution('Products.CMFPlone').version >= '5.1'


class TestFunctionalMigrations(unittest.TestCase):
    """Run an upgrade from a real Plone 4.0 ZEXP to 5.2.
    Then test that various things are set up correctly.
    """

    layer = REAL_UPGRADE_FUNCTIONAL

    def setUp(self):
        self.portal = self.layer['app'].plone

    def testFullyUpgraded(self):
        self.assertFalse(self.portal.portal_migration.needUpgrading())

    def testCanRenderHomepage(self):
        browser = Browser(self.layer['app'])
        portalURL = self.portal.absolute_url()
        browser.open(portalURL)
        self.assertTrue('Plone' in browser.contents)

    def testToolsAreRemoved(self):
        self.assertFalse('portal_css' in self.portal)
        self.assertFalse('portal_javascripts' in self.portal)


def test_suite():
    # Skip these tests on Plone < 5.1
    if not PLONE_51:
        return unittest.TestSuite()

    suite = unittest.TestSuite()
    suite.addTest(
        unittest.makeSuite(TestFunctionalMigrations)
        )
    return suite
