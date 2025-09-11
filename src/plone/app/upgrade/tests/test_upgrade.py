from importlib.metadata import version
from plone.app.upgrade.tests.base import MigrationTest
from plone.app.upgrade.utils import version_match
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.factory import _DEFAULT_PROFILE
from unittest import mock

import unittest


IS_CMFPLONE_DEV = "dev" in version("Products.CMFPlone")


class TestUpgrade(MigrationTest):
    def afterSetUp(self):
        self.setup = getToolByName(self.portal, "portal_setup")

    @unittest.skipUnless(IS_CMFPLONE_DEV, reason="Only run with CMFPlone checkouts")
    def testListUpgradeSteps(self):
        # There should be no upgrade steps from the current version
        upgrades = self.setup.listUpgrades(_DEFAULT_PROFILE)
        self.assertEqual(len(upgrades), 0)

    def testProfileVersion(self):
        # The profile version for the base profile should be the same
        # as the file system version and the instance version
        self.setup = getToolByName(self.portal, "portal_setup")

        current = self.setup.getVersionForProfile(_DEFAULT_PROFILE)
        current = tuple(current.split("."))
        last = self.setup.getLastVersionForProfile(_DEFAULT_PROFILE)
        self.assertEqual(last, current)

    @mock.patch("plone.app.upgrade.utils.plone_version", "5.0b1")
    def testVersionMatch(self):
        self.assertFalse(version_match("2.5"))
        self.assertFalse(version_match("3.1b1"))
        self.assertFalse(version_match("5.2.b1"))
        self.assertTrue(version_match("5.0a3.dev0"))
        self.assertTrue(version_match("5.0b1.dev0"))
        self.assertTrue(version_match("5.0b3"))
        self.assertTrue(version_match("5.0"))

    def testDoUpgrades(self):
        self.setRoles(["Manager"])

        # Python 3 is only supported on 5.2+.
        # This means you can not upgrade from 5.1 or earlier.
        start_profile = "5200"
        self.setup.setLastVersionForProfile(_DEFAULT_PROFILE, start_profile)
        upgrades = self.setup.listUpgrades(_DEFAULT_PROFILE)
        self.assertTrue(len(upgrades) > 0)

        request = self.portal.REQUEST
        request.form["profile_id"] = _DEFAULT_PROFILE

        steps = []
        for u in upgrades:
            if isinstance(u, list):
                steps.extend([s["id"] for s in u])
            else:
                steps.append(u["id"])

        request.form["upgrades"] = steps
        self.setup.manage_doUpgrades(request=request)

        # And we have reached our current profile version
        current = self.setup.getVersionForProfile(_DEFAULT_PROFILE)
        current = tuple(current.split("."))
        last = self.setup.getLastVersionForProfile(_DEFAULT_PROFILE)
        if IS_CMFPLONE_DEV:
            self.assertEqual(last, current)

        # There are no more upgrade steps available
        upgrades = self.setup.listUpgrades(_DEFAULT_PROFILE)
        self.assertEqual(len(upgrades), 0)

    def test_upgrade_tinymce_menubar(self):

        from packaging.version import parse
        from plone.app.upgrade.utils import plone_version
        from plone.app.upgrade.v61.final import upgrade_registry_tinymce_menubar
        from plone.base.interfaces.controlpanel import ITinyMCESchema
        from plone.registry import field
        from plone.registry.interfaces import IRegistry
        from plone.registry.record import Record
        from zope.component import getUtility

        version = parse(plone_version)
        if version.major < 6 or version.minor < 1:
            # don't execute the test for Plone < 6.1
            return

        registry = getUtility(IRegistry)

        # for test we delete the original record
        del registry.records["plone.menubar"]

        # and set a new dummy list record
        record = registry.records["plone.menubar"] = Record(
            field.List(
                title="Test",
                min_length=0,
                max_length=10,
                value_type=field.TextLine(title="Value"),
            ),
            ["Test1", "Test2"],
        )

        # run the upgrade helper function
        upgrade_registry_tinymce_menubar(self.setup)

        # the interface of the record should be `ITinyMCESchema`
        self.assertTrue(record.interface, ITinyMCESchema)

        # the value should be a string, not a list
        self.assertTrue(record.value, "Test1 Test2")


def test_suite():
    import unittest

    return unittest.TestSuite(
        (unittest.defaultTestLoader.loadTestsFromTestCase(TestUpgrade),)
    )
