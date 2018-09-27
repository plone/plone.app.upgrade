# -*- coding: utf-8 -*-
from plone.app.testing import PLONE_INTEGRATION_TESTING
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.interfaces import IFilterSchema
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
        registry[plv]['plone-toolbar-font-secundary'] = 'Foo'
        if 'plone-toolbar-font-secondary' in registry[plv]:
            del registry[plv]['plone-toolbar-font-secondary']

        # start testing
        _fix_typo_in_toolbar_less_variable(self)
        self.assertEqual(
            registry[plv]['plone-toolbar-font-secondary'],
            'Foo',
        )
        self.assertNotIn('plone-toolbar-font-secundary', registry[plv])


class UpgradePortalTransforms51beta4to51beta5Test(unittest.TestCase):
    layer = PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        self.pt = self.portal.portal_transforms
        registry = getUtility(IRegistry)
        self.settings = registry.forInterface(
            IFilterSchema, prefix='plone')

    def test_migrate_safe_html_settings(self):
        from plone.app.upgrade.v51.betas import \
            move_safe_html_settings_to_registry
        self.pt.safe_html._config['valid_tags'] = {'b': 1, 'img': 0}
        move_safe_html_settings_to_registry(self.portal)
        # make sure the boolean setting (used to mark open tags like img)
        # is ignored. Only works in 5.1
        if getattr(self.settings, 'valid_tags', None):
            self.assertEqual(self.settings.valid_tags, ['b', 'img'])


def test_suite():
    # Skip these tests on Plone 4
    if not six.PY2 or not PLONE_5:
        return unittest.TestSuite()

    suite = unittest.TestSuite()
    suite.addTest(
        unittest.makeSuite(UpgradeRegistry503to51alpha1Test),
    )
    suite.addTest(
        unittest.makeSuite(UpgradePortalTransforms51beta4to51beta5Test),
    )
    return suite
