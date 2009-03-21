from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.tests.base import MigrationTest

from plone.app.upgrade.v30.final_three0x import installNewModifiers


class TestMigrations_v3_0(MigrationTest):

    def afterSetUp(self):
        self.actions = self.portal.portal_actions
        self.skins = self.portal.portal_skins
        self.types = self.portal.portal_types
        self.workflow = self.portal.portal_workflow
        self.properties = getToolByName(self.portal, 'portal_properties')

    def testInstallNewModifiers(self):
        # ensure the new modifiers are installed
        modifiers = self.portal.portal_modifier
        self.failUnless('AbortVersioningOfLargeFilesAndImages' in
                                                          modifiers.objectIds())
        modifiers.manage_delObjects(['AbortVersioningOfLargeFilesAndImages',
                                     'SkipVersioningOfLargeFilesAndImages'])
        self.failIf('AbortVersioningOfLargeFilesAndImages' in
                                                          modifiers.objectIds())
        installNewModifiers(self.portal)
        self.failUnless('AbortVersioningOfLargeFilesAndImages' in
                                                          modifiers.objectIds())
        self.failUnless('SkipVersioningOfLargeFilesAndImages' in
                                                          modifiers.objectIds())

    def testInstallNewModifiersTwice(self):
        # ensure that we get no errors when run twice
        modifiers = self.portal.portal_modifier
        installNewModifiers(self.portal)
        installNewModifiers(self.portal)

    def testInstallNewModifiersDoesNotStompChanges(self):
        # ensure that reinstalling doesn't kill customizations
        modifiers = self.portal.portal_modifier
        modifiers.AbortVersioningOfLargeFilesAndImages.max_size = 1000
        installNewModifiers(self.portal)
        self.assertEqual(modifiers.AbortVersioningOfLargeFilesAndImages.max_size,
                         1000)

    def testInstallNewModifiersNoTool(self):
        # make sure there are no errors if the tool is missing
        self.portal._delObject('portal_modifier')
        installNewModifiers(self.portal)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestMigrations_v3_0))
    return suite
