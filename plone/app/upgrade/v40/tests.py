from Products.CMFCore.ActionInformation import Action
from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.tests.base import MigrationTest


class TestMigrations_v4_0alpha1(MigrationTest):

    profile = "profile-plone.app.upgrade.v40:3-4alpha1"

    def testProfile(self):
        # This tests the whole migration profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.failUnless(True)

    def testPngContentIcons(self):
        tt = getToolByName(self.portal, "portal_types")
        tt.Document.content_icon = "document_icon.gif"
        loadMigrationProfile(self.portal, self.profile, ('typeinfo', ))
        self.assertEqual(tt.Document.content_icon, "document_icon.png")


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestMigrations_v4_0alpha1))
    return suite
