from plone.app.testing import PLONE_INTEGRATION_TESTING
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import unittest


FULLSCREEN_DEFER = "plone.bundles/plone-fullscreen.load_defer"


class Various62Test(unittest.TestCase):
    layer = PLONE_INTEGRATION_TESTING

    def test_defer_fullscreen_bundle(self):
        from plone.app.upgrade.v62.final import defer_fullscreen_bundle

        registry = getUtility(IRegistry)
        registry[FULLSCREEN_DEFER] = False
        defer_fullscreen_bundle(self.layer["portal"].portal_setup)
        self.assertTrue(registry[FULLSCREEN_DEFER])

    def test_defer_fullscreen_bundle_without_the_record(self):
        from plone.app.upgrade.v62.final import defer_fullscreen_bundle

        registry = getUtility(IRegistry)
        prefix = "plone.bundles/plone-fullscreen."
        for key in [key for key in registry.records if key.startswith(prefix)]:
            del registry.records[key]
        defer_fullscreen_bundle(self.layer["portal"].portal_setup)
        self.assertNotIn(FULLSCREEN_DEFER, registry.records)
