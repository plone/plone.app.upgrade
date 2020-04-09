# -*- coding: utf-8 -*-
from DateTime import DateTime
from pkg_resources import get_distribution
from pkg_resources import parse_version
from plone.app.testing import PLONE_INTEGRATION_TESTING
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IMarkupSchema
from zope.component import getUtility

import unittest


class UpgradeMemberData51to52Test(unittest.TestCase):
    layer = PLONE_INTEGRATION_TESTING

    def test_rebuild_member_data(self):
        portal = self.layer['portal']
        from plone.app.upgrade.v52.alphas import rebuild_memberdata

        rebuild_memberdata(portal)
        tool = getToolByName(portal, 'portal_memberdata')
        self.assertIn('test_user_1_', tool._members.keys())


class Various52Test(unittest.TestCase):
    layer = PLONE_INTEGRATION_TESTING

    def test_rebuild_redirections(self):
        # Until at least 5.2rc1, redirection values were simple paths,
        # now they are tuples.  The upgrade step rebuilds the information.
        # (The code can at the moment handle old-style and new-style,
        # but rebuilding is still good.)
        from plone.app.redirector.interfaces import IRedirectionStorage
        from plone.app.upgrade.v52.final import rebuild_redirections

        storage = getUtility(IRedirectionStorage)
        # add old-style redirect directly in internal structure:
        old = '/plone/old'
        new = '/plone/new'
        storage._paths[old] = new
        # get_full mocks a new-style redirect,
        # though with None instead of a DateTime, and manual always True.
        self.assertTupleEqual(storage.get_full(old), (new, None, True))
        portal = self.layer['portal']
        # Run the rebuild, and keep track of time before and after.
        time1 = DateTime()
        rebuild_redirections(portal.portal_setup)
        time2 = DateTime()
        # The basic information and usage has not changed:
        self.assertIn(old, storage)
        self.assertListEqual(storage.redirects(new), [old])
        self.assertEqual(storage.get(old), new)
        self.assertEqual(storage[old], new)
        # The internal structure is now a tuple:
        redirect = storage._paths[old]
        self.assertIsInstance(redirect, tuple)
        # The first item in the tuple is the target path.
        self.assertEqual(redirect[0], new)
        # The current DateTime is set as the creation time of the redirect.
        self.assertIsInstance(redirect[1], DateTime)
        self.assertTrue(time1 < redirect[1] < time2)
        # Existing migrations are marked as manual,
        # because we have no way of knowing if it is automatic or nor.
        self.assertEqual(redirect[2], True)
        # get_full now returns the real information
        self.assertTupleEqual(storage.get_full(old), redirect)


class UpgradePortalTransforms521to522Test(unittest.TestCase):
    layer = PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.pt = self.portal.portal_transforms
        registry = getUtility(IRegistry)
        self.settings = registry.forInterface(IMarkupSchema, prefix='plone')

    def test_migrate_markup_settings(self):
        from plone.app.upgrade.v52.final import \
            move_markdown_transform_settings_to_registry
        self.pt.markdown_to_html._config['enabled_extensions'] = [
            'markdown.extensions.fenced_code',
            'markdown.extensions.nl2br',
            'markdown.extensions.extra',
        ]
        move_markdown_transform_settings_to_registry(self.portal)
        if getattr(self.settings, 'markdown_extensions', None):
            self.assertEqual(
                self.settings.markdown_extensions,
                [
                    'markdown.extensions.fenced_code',
                    'markdown.extensions.nl2br',
                    'markdown.extensions.extra',
                ]
            )


def test_suite():
    # Skip these tests on Plone < 5.2a1
    plone_version = get_distribution('Products.CMFPlone').version
    if not parse_version(plone_version) >= parse_version('5.2a1'):
        return unittest.TestSuite()

    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UpgradeMemberData51to52Test))
    suite.addTest(unittest.makeSuite(Various52Test))
    suite.addTest(unittest.makeSuite(UpgradePortalTransforms521to522Test))
    return suite
