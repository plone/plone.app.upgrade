from plone.app.upgrade.tests.base import MigrationTest
from plone.browserlayer.utils import registered_layers
from plone.browserlayer.utils import unregister_layer

import unittest

try:
    import plone.app.contentrules  # noqa: F401

    HAS_CONTENTRULES = True
except ImportError:
    # Core add-on since Plone 6.3, may not be installed.
    HAS_CONTENTRULES = False

PROFILE = "plone.app.contentrules:default"


@unittest.skipUnless(HAS_CONTENTRULES, "plone.app.contentrules is not installed")
class TestInstallContentrulesProfile(MigrationTest):
    def afterSetUp(self):
        self.setup = self.portal.portal_setup
        if not self.setup.profileExists(PROFILE):
            self.skipTest("plone.app.contentrules has no default profile")
        # Simulate a site from before the profile existed.
        self.setup.unsetLastVersionForProfile(PROFILE)
        try:
            unregister_layer("plone.app.contentrules")
        except KeyError:
            pass

    def _layer_names(self):
        return [layer.__identifier__ for layer in registered_layers()]

    def test_installs_layer_and_version(self):
        from plone.app.upgrade.v63.alpha import install_contentrules_profile

        install_contentrules_profile(self.setup)
        self.assertIn(
            "plone.app.contentrules.browser.interfaces.IPloneAppContentrulesLayer",
            self._layer_names(),
        )
        self.assertEqual(self.setup.getLastVersionForProfile(PROFILE), ("7000",))

    def test_keeps_existing_rules(self):
        from plone.app.contentrules.rule import Rule
        from plone.app.upgrade.v63.alpha import install_contentrules_profile
        from plone.contentrules.engine.interfaces import IRuleStorage
        from zope.component import getUtility

        storage = getUtility(IRuleStorage)
        storage["keep-me"] = Rule()
        install_contentrules_profile(self.setup)
        self.assertIs(getUtility(IRuleStorage), storage)
        self.assertIn("keep-me", storage)

    def test_idempotent(self):
        from plone.app.upgrade.v63.alpha import install_contentrules_profile

        install_contentrules_profile(self.setup)
        install_contentrules_profile(self.setup)
        self.assertEqual(self.setup.getLastVersionForProfile(PROFILE), ("7000",))

    def test_skips_when_profile_missing(self):
        from plone.app.upgrade.v63 import alpha
        from unittest import mock

        with mock.patch.object(self.setup, "profileExists", return_value=False):
            alpha.install_contentrules_profile(self.setup)
        self.assertEqual(self.setup.getLastVersionForProfile(PROFILE), "unknown")
        self.assertNotIn(
            "plone.app.contentrules.browser.interfaces.IPloneAppContentrulesLayer",
            self._layer_names(),
        )
