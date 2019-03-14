# -*- coding: utf-8 -*-
from pkg_resources import get_distribution
from pkg_resources import parse_version
from plone.app.testing import PLONE_INTEGRATION_TESTING
from Products.CMFCore.utils import getToolByName

import unittest


class UpgradeMemberData51to52Test(unittest.TestCase):
    layer = PLONE_INTEGRATION_TESTING

    def test_rebuild_member_data(self):
        portal = self.layer['portal']
        from plone.app.upgrade.v52.alphas import rebuild_memberdata
        rebuild_memberdata(portal)
        tool = getToolByName(portal, 'portal_memberdata')
        self.assertIn(
            'test_user_1_', tool._members.keys())


def test_suite():
    # Skip these tests on Plone < 5.2a1
    plone_version = get_distribution('Products.CMFPlone').version
    if not parse_version(plone_version) >= parse_version('5.2a1'):
        return unittest.TestSuite()

    suite = unittest.TestSuite()
    suite.addTest(
        unittest.makeSuite(UpgradeMemberData51to52Test),
    )
    return suite
