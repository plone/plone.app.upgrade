# -*- coding: utf-8 -*-
from plone.app.testing import PLONE_INTEGRATION_TESTING
from zope.component import getUtility

import unittest

try:
    from Products.CMFPlone.factory import _IMREALLYPLONE5
    _IMREALLYPLONE5  # pyflakes
except ImportError:
    PLONE_5 = False
else:
    PLONE_5 = True


class UpgradeRegistry503to51alpha1Test(unittest.TestCase):
    """test registry changes
    """

    layer = PLONE_INTEGRATION_TESTING

    def test_migrate_less_variable_typo(self):
        from plone.app.upgrade.v51.alphas import \
            _fix_typo_in_toolbar_less_variable
        from plone.registry.interfaces import IRegistry
        registry = getUtility(IRegistry)

        # set to a defined state
        plv = 'plone.lessvariables'
        registry[plv]['plone-toolbar-font-secundary'] = "Foo"
        if 'plone-toolbar-font-secondary' in registry[plv]:
            del registry[plv]['plone-toolbar-font-secondary']

        # start testing
        _fix_typo_in_toolbar_less_variable(self)
        self.assertEqual(
            registry[plv]['plone-toolbar-font-secondary'],
            'Foo',
        )
        self.assertTrue(
            'plone-toolbar-font-secundary' not in registry[plv]
        )


def test_suite():
    # Skip these tests on Plone 4
    if not PLONE_5:
        return unittest.TestSuite()

    suite = unittest.TestSuite()
    suite.addTest(
        unittest.makeSuite(UpgradeRegistry503to51alpha1Test)
    )
    return suite
