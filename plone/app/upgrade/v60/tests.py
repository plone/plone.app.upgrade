from plone.app.testing import PLONE_INTEGRATION_TESTING
from plone.dexterity.interfaces import IDexterityFTI
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility

import re
import unittest


class Various60UnitTest(unittest.TestCase):

    def test_fix_mimetypes_registry_context_manager(self):
        """Check that a glob registered with a pattern that throws a re.error
        is fixed.
        """
        from plone.app.upgrade.v60.final import BogusPattern
        from plone.app.upgrade.v60.final import TemporaryReCompile

        # If we pass to recompile an invalid pattern, it will raise an error.
        with self.assertRaises(re.error):
            re.compile("[z-a]")

        # But if we are in the context manager, it will catch the error and return
        # an instance of BogusPattern.
        with TemporaryReCompile():
            compiled_pattern = re.compile("[z-a]")
            self.assertIsInstance(compiled_pattern, BogusPattern)
            self.assertEqual(compiled_pattern.pattern, "[z-a]")

        # When we are out of the context manager, the original re.compile is restored.
        with self.assertRaises(re.error):
            re.compile("[z-a]")


class Various60Test(unittest.TestCase):
    layer = PLONE_INTEGRATION_TESTING

    def test_add_new_image_scales(self):
        from plone.app.upgrade.v60.alphas import add_new_image_scales

        # These new scales should get added:
        new_scales = [
            "teaser 600:65536",
            "larger 1000:65536",
            "great 1200:65536",
            "huge 1600:65536",
        ]
        portal = self.layer["portal"]
        setup = getToolByName(portal, "portal_setup")
        registry = getUtility(IRegistry)

        # Call the upgrade step.
        add_new_image_scales(setup)
        record = registry.records["plone.allowed_sizes"]
        for scale in new_scales:
            self.assertIn(scale, record.value)

        # If scales with the given name already exist, do not change them.
        record.value = [
            "mini 200:200",
            "teaser 42:42",
            "maxi 200:400",
        ]
        add_new_image_scales(setup)
        self.assertIn("mini 200:200", record.value)
        self.assertIn("teaser 42:42", record.value)
        self.assertNotIn("teaser 600:65536", record.value)
        self.assertIn("huge 1600:65536", record.value)

        # If we make a change, we sort by width, then height.
        self.assertEqual(
            record.value,
            [
                "huge 1600:65536",
                "great 1200:65536",
                "larger 1000:65536",
                "maxi 200:400",
                "mini 200:200",
                "teaser 42:42",
            ],
        )

        # If we do not make a change, we also do not change the sort order.
        # As value, store the new scales alphabetically ordered.
        record.value = sorted(new_scales)
        add_new_image_scales(setup)
        self.assertEqual(record.value, sorted(new_scales))

        # Check that the upgrade does not break easily.
        record.value = [
            "too many spaces 100:100",
            "not_enough_spaces200:200",
            "too_many_colons 300:300:400",
            "not_enough_many_colons 500",
            "good 600:600",
            " space 700:700 ",
            "# just a comment",
            "or an empty line:",
            "",
        ]
        # The biggest is is that this does not throw an error:
        add_new_image_scales(setup)
        # The bad scales will be at the end.
        self.assertEqual(
            record.value,
            [
                "huge 1600:65536",
                "great 1200:65536",
                "larger 1000:65536",
                " space 700:700 ",
                "teaser 600:65536",
                "good 600:600",
                "too many spaces 100:100",
                "not_enough_spaces200:200",
                "too_many_colons 300:300:400",
                "not_enough_many_colons 500",
                "# just a comment",
                "or an empty line:",
            ],
        )

    def test_upgrade_plone_module_profiles_dexterity(self):
        from plone.app.upgrade.v60.alphas import upgrade_plone_module_profiles

        portal = self.layer["portal"]
        setup = getToolByName(portal, "portal_setup")

        # We expect plone.app.dexterity to be at least at version 2007.
        # The version is a tuple like ("2007",)
        profile_id = "plone.app.dexterity:default"
        self.assertGreaterEqual(setup.getLastVersionForProfile(profile_id), ("2007",))

        # Calling the upgrade step should not change this.
        upgrade_plone_module_profiles(setup)
        self.assertGreaterEqual(setup.getLastVersionForProfile(profile_id), ("2007",))

        # Pretend that we are at an earlier version.
        # This should result in an upgrade to the exact requested version,
        # even when steps exist to upgrade it to a much newer version.
        setup.setLastVersionForProfile(profile_id, "2005")
        upgrade_plone_module_profiles(setup)
        self.assertEqual(setup.getLastVersionForProfile(profile_id), ("2007",))

        # Pretend that we are at a later version.
        # The version should stay the same then, no downgrading.
        setup.setLastVersionForProfile(profile_id, "9999")
        upgrade_plone_module_profiles(setup)
        self.assertEqual(setup.getLastVersionForProfile(profile_id), ("9999",))

    def test_upgrade_plone_module_profiles_multilingual(self):
        from plone.app.upgrade.v60.alphas import upgrade_plone_module_profiles
        from Products.GenericSetup.tool import UNKNOWN

        portal = self.layer["portal"]
        setup = getToolByName(portal, "portal_setup")

        # Upgrade steps are only run when the profile is already active.
        # Multilingual support is not active by default.
        profile_id = "plone.app.multilingual:default"
        self.assertEqual(setup.getLastVersionForProfile(profile_id), UNKNOWN)
        upgrade_plone_module_profiles(setup)
        self.assertEqual(setup.getLastVersionForProfile(profile_id), UNKNOWN)

    def test_rename_dexteritytextindexer_behavior(self):
        from plone.app.upgrade.v60.betas import rename_dexteritytextindexer_behavior

        portal = self.layer["portal"]

        fti = getUtility(IDexterityFTI, name="Document")

        original_behaviors = fti.behaviors
        expected_behaviors = original_behaviors + ("plone.textindexer",)
        # If the dexteritytextindexer behavior is not present nothing should change
        rename_dexteritytextindexer_behavior(portal)
        self.assertTupleEqual(fti.behaviors, original_behaviors)

        # If the dexteritytextindexer behavior is present it should be renamed
        fti.behaviors = fti.behaviors + ("collective.dexteritytextindexer",)
        rename_dexteritytextindexer_behavior(portal)
        self.assertTupleEqual(fti.behaviors, expected_behaviors)

        # If the old and new dexteritytextindexer behaviors are present,
        # we should only have the new one
        fti.behaviors = fti.behaviors + ("collective.dexteritytextindexer",)
        rename_dexteritytextindexer_behavior(portal)
        self.assertTupleEqual(fti.behaviors, expected_behaviors)

        # Check that the fix also works with the interface identifier
        fti.behaviors = original_behaviors + (
            "collective.dexteritytextindexer.behavior.IDexterityTextIndexer",
        )
        rename_dexteritytextindexer_behavior(portal)
        self.assertTupleEqual(fti.behaviors, expected_behaviors)

    def test_fix_mimetypes_registry_python_27(self):
        """Check that the old style patterns coming from Python 2.7 will be fixed."""
        from plone.app.upgrade.v60.final import cleanup_mimetypes_registry
        from Products.MimetypesRegistry.MimeTypeItem import MimeTypeItem

        class Pattern27:
            """A class that has a pattern attribute that mimics
            the ones produced in Python 2.7
            """

            pattern = r"foo\Z(?ms)"

        portal = self.layer["portal"]
        mtr = getToolByName(portal, "mimetypes_registry")
        mimetype = (MimeTypeItem("bogus", mimetypes=["foo/bar"]),)
        mtr.globs["bogus"] = (Pattern27, mimetype)

        # Check that the old pattern is changed after running the fix.
        with unittest.mock.patch("plone.app.upgrade.v60.final.logger") as mock_logger:
            cleanup_mimetypes_registry(portal)
            self.assertEqual(mock_logger.info.call_count, 2)
            self.assertTupleEqual(
                mock_logger.method_calls[1].args, ("%r globs were fixed", 1)
            )

        self.assertTupleEqual(
            mtr.globs["bogus"], (re.compile("(?s:bogus)\\Z"), mimetype)
        )

    def test_fix_mimetypes_registry_bogus_pattern(self):
        """Check that a glob with a pattern that is an instance of BogusPattern
        will be fixed.
        """
        from plone.app.upgrade.v60.final import BogusPattern
        from plone.app.upgrade.v60.final import cleanup_mimetypes_registry
        from Products.MimetypesRegistry.MimeTypeItem import MimeTypeItem

        portal = self.layer["portal"]
        mtr = getToolByName(portal, "mimetypes_registry")
        mimetype = (MimeTypeItem("bogus", mimetypes=["foo/bar"]),)
        mtr.globs["bogus"] = (BogusPattern("bogus", re.error("bogus")), mimetype)

        # Check that the old pattern is changed after running the fix.
        with unittest.mock.patch("plone.app.upgrade.v60.final.logger") as mock_logger:
            cleanup_mimetypes_registry(portal)
            self.assertEqual(mock_logger.info.call_count, 2)
            self.assertTupleEqual(
                mock_logger.method_calls[1].args, ("%r globs were fixed", 1)
            )

        self.assertTupleEqual(
            mtr.globs["bogus"], (re.compile("(?s:bogus)\\Z"), mimetype)
        )
