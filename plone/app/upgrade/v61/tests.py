from plone.app.testing import PLONE_INTEGRATION_TESTING
from Products.CMFCore.utils import getToolByName
from Products.MimetypesRegistry.MimeTypeItem import MimeTypeItem

import re
import unittest


class Various61UnitTests(unittest.TestCase):

    def test_fix_mimetypes_registry_context_manager(self):
        """Check that a glob registered with a pattern that throws a re.error
        is fixed.
        """
        from plone.app.upgrade.v61.final import BogusPattern
        from plone.app.upgrade.v61.final import TemporaryReCompile

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


class Various61Test(unittest.TestCase):
    layer = PLONE_INTEGRATION_TESTING

    def test_fix_mimetypes_registry_python_27(self):
        """Check that the old style patterns coming from Python 2.7 will be fixed."""

        from plone.app.upgrade.v61.final import cleanup_mimetypes_registry

        class Pattern27:
            """A class that has a pattern attribute that mimics
            the ones produced in Python 2.7
            """

            pattern = "foo\Z(?ms)"

        portal = self.layer["portal"]
        mtr = getToolByName(portal, "mimetypes_registry")
        mimetype = (MimeTypeItem("bogus", mimetypes=["foo/bar"]),)
        mtr.globs["bogus"] = (Pattern27, mimetype)

        # Check that the old pattern is changed after running the fix.
        with unittest.mock.patch("plone.app.upgrade.v61.final.logger") as mock_logger:
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
        from plone.app.upgrade.v61.final import BogusPattern
        from plone.app.upgrade.v61.final import cleanup_mimetypes_registry

        portal = self.layer["portal"]
        mtr = getToolByName(portal, "mimetypes_registry")
        mimetype = (MimeTypeItem("bogus", mimetypes=["foo/bar"]),)
        mtr.globs["bogus"] = (BogusPattern("bogus", re.error("bogus")), mimetype)

        # Check that the old pattern is changed after running the fix.
        with unittest.mock.patch("plone.app.upgrade.v61.final.logger") as mock_logger:
            cleanup_mimetypes_registry(portal)
            self.assertEqual(mock_logger.info.call_count, 2)
            self.assertTupleEqual(
                mock_logger.method_calls[1].args, ("%r globs were fixed", 1)
            )

        self.assertTupleEqual(
            mtr.globs["bogus"], (re.compile("(?s:bogus)\\Z"), mimetype)
        )
