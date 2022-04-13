from DateTime import DateTime
from pkg_resources import get_distribution
from pkg_resources import parse_version
from plone.app.testing import PLONE_INTEGRATION_TESTING
from plone.registry import field
from plone.registry import Record
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IMarkupSchema
from zope.component import getUtility

import unittest


class UpgradeMemberData51to52Test(unittest.TestCase):
    layer = PLONE_INTEGRATION_TESTING

    def test_rebuild_member_data(self):
        portal = self.layer["portal"]
        from plone.app.upgrade.v52.alphas import rebuild_memberdata

        rebuild_memberdata(portal)
        tool = getToolByName(portal, "portal_memberdata")
        self.assertIn("test_user_1_", tool._members.keys())


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
        old = "/plone/old"
        new = "/plone/new"
        storage._paths[old] = new
        # get_full mocks a new-style redirect,
        # though with None instead of a DateTime, and manual always True.
        self.assertTupleEqual(storage.get_full(old), (new, None, True))
        portal = self.layer["portal"]
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


class SiteLogoTest(unittest.TestCase):
    """Site logo was ASCII field in 5.1, and is Bytes field in 5.2.

    zope.schema.ASCII inherits from NativeString.
    With Python 2 this is the same as Bytes, but with Python 3 not:
    you get a WrongType error when saving the site-controlpanel.

    We have several situations that should result in the fix being applied:

    1. Migration from Plone 5.1 to 5.2 on Python 2.7.
    2. Migration from Plone 5.2.2 on Python 2.7 (where the logo is technically broken, but still works)
       to 5.2.3 (which contains this upgrade step) on Python 2.7.
       This is in fact the same as situation 1.
    3. Migration from Plone 5.2.2 on Python 3 (where the logo is really broken, at least for writing)
       to 5.2.3 (which contains this upgrade step).

    On Python 3 there is a definite difference between the two types of field.
    Tricky here may be that we should make sure that the fix is also applied on Python 2,
    where ASCII and Bytes are still the same.
    Ah, no problem after all: zope.schema.ASCII/Bytes may be the same,
    but plone.registry.fields.ASCII/Bytes are always different.
    """

    layer = PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.registry = getUtility(IRegistry)

    def test_current_site_logo(self):
        # Check that we understand the current situation correctly.
        from plone.app.upgrade.v52.final import migrate_site_logo_from_ascii_to_bytes
        from zope.schema.interfaces import WrongType

        record = self.registry.records["plone.site_logo"]
        self.assertIsInstance(record.field, field.Bytes)
        self.assertIsNone(record.value)
        with self.assertRaises(WrongType):
            record.value = "abc"
        record.value = b"ABC"
        self.assertEqual(record.value, b"ABC")
        # Migrating does nothing.
        migrate_site_logo_from_ascii_to_bytes(self.portal)
        record = self.registry.records["plone.site_logo"]
        self.assertIsInstance(record.field, field.Bytes)
        self.assertIsInstance(record.value, bytes)
        self.assertEqual(record.value, b"ABC")

    def test_missing_site_logo_record(self):
        # Test that the migration adds the record if for some reason it is missing.
        from plone.app.upgrade.v52.final import migrate_site_logo_from_ascii_to_bytes

        del self.registry.records["plone.site_logo"]
        migrate_site_logo_from_ascii_to_bytes(self.portal)
        record = self.registry.records["plone.site_logo"]
        self.assertIsInstance(record.field, field.Bytes)
        self.assertIsNone(record.value)

    def test_site_logo_empty(self):
        from plone.app.upgrade.v52.final import migrate_site_logo_from_ascii_to_bytes

        del self.registry.records["plone.site_logo"]
        record_51 = Record(field.ASCII())
        self.registry.records["plone.site_logo"] = record_51
        # Migrate.
        migrate_site_logo_from_ascii_to_bytes(self.portal)
        record = self.registry.records["plone.site_logo"]
        self.assertIsInstance(record.field, field.Bytes)
        self.assertIsNone(record.value)

    def test_site_logo_text(self):
        from plone.app.upgrade.v52.final import migrate_site_logo_from_ascii_to_bytes

        del self.registry.records["plone.site_logo"]
        record_51 = Record(field.ASCII())
        record_51.value = "native string"
        self.registry.records["plone.site_logo"] = record_51
        # Migrate.
        migrate_site_logo_from_ascii_to_bytes(self.portal)
        record = self.registry.records["plone.site_logo"]
        self.assertIsInstance(record.field, field.Bytes)
        self.assertIsInstance(record.value, bytes)
        self.assertEqual(record.value, b"native string")

    def test_migrate_record_from_ascii_to_bytes_with_prefix(self):
        # This is the more general fixer from ASCII to Bytes.
        from plone.app.upgrade.v52.final import migrate_record_from_ascii_to_bytes
        from zope import schema
        from zope.interface import Interface

        class ITest(Interface):
            testfield = schema.ASCII()

        self.registry.registerInterface(ITest, prefix="testing")
        record = self.registry.records["testing.testfield"]
        record.value = "native string"
        self.assertIsInstance(record.field, field.ASCII)

        # Now change the field definition to Bytes.
        # It is not enough to override the field, we must recreate the interface.
        # ITest.testfield = schema.Bytes()

        class ITest(Interface):
            testfield = schema.Bytes()

        # These variations all seem to work:
        migrate_record_from_ascii_to_bytes("testing.testfield", ITest, prefix="testing")
        # migrate_record_from_ascii_to_bytes("testfield", ITest, prefix="testing")
        record = self.registry.records["testing.testfield"]
        self.assertIsInstance(record.field, field.Bytes)
        self.assertIsInstance(record.value, bytes)
        self.assertEqual(record.value, b"native string")

    def test_migrate_record_from_ascii_to_bytes_without_prefix(self):
        # This is the more general fixer from ASCII to Bytes.
        from plone.app.upgrade.v52.final import migrate_record_from_ascii_to_bytes
        from zope import schema
        from zope.interface import Interface

        class ITest(Interface):
            testfield = schema.ASCII()

        self.registry.registerInterface(ITest)
        record_name = f"{ITest.__identifier__}.testfield"
        record = self.registry.records[record_name]
        record.value = "native string"
        self.assertIsInstance(record.field, field.ASCII)

        # Now change the field definition to Bytes.
        # It is not enough to override the field, we must recreate the interface.
        # ITest.testfield = schema.Bytes()

        class ITest(Interface):
            testfield = schema.Bytes()

        # These variations all seem to work, so choose the easiest one:
        migrate_record_from_ascii_to_bytes("testfield", ITest)
        # migrate_record_from_ascii_to_bytes("testfield", ITest, prefix=ITest.__identifier__)
        # migrate_record_from_ascii_to_bytes(record_name, ITest)
        # migrate_record_from_ascii_to_bytes(record_name, ITest, prefix=ITest.__identifier__)
        record = self.registry.records[record_name]
        self.assertIsInstance(record.field, field.Bytes)
        self.assertIsInstance(record.value, bytes)
        self.assertEqual(record.value, b"native string")


class UpgradePortalTransforms521to522Test(unittest.TestCase):
    layer = PLONE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        self.pt = self.portal.portal_transforms
        registry = getUtility(IRegistry)
        self.settings = registry.forInterface(IMarkupSchema, prefix="plone")

    def test_migrate_markup_settings(self):
        from plone.app.upgrade.v52.final import (
            move_markdown_transform_settings_to_registry,
        )

        self.pt.markdown_to_html._config["enabled_extensions"] = [
            "markdown.extensions.fenced_code",
            "markdown.extensions.nl2br",
            "markdown.extensions.extra",
        ]
        move_markdown_transform_settings_to_registry(self.portal)
        if getattr(self.settings, "markdown_extensions", None):
            self.assertEqual(
                self.settings.markdown_extensions,
                [
                    "markdown.extensions.fenced_code",
                    "markdown.extensions.nl2br",
                    "markdown.extensions.extra",
                ],
            )


def test_suite():
    # Skip these tests on Plone < 5.2a1
    plone_version = get_distribution("Products.CMFPlone").version
    if not parse_version(plone_version) >= parse_version("5.2a1"):
        return unittest.TestSuite()

    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(UpgradeMemberData51to52Test))
    suite.addTest(unittest.makeSuite(Various52Test))
    suite.addTest(unittest.makeSuite(SiteLogoTest))
    suite.addTest(unittest.makeSuite(UpgradePortalTransforms521to522Test))
    return suite
