from plone.app.upgrade.tests.base import MigrationTest
from plone.app.upgrade.v32.betas import three1_beta1

class TestMigrations_v3_2(MigrationTest):

    def afterSetUp(self):
        self.qi = self.portal.portal_quickinstaller
        self.actions = self.portal.portal_actions
        self.migration = self.portal.portal_migration

    def testIterateActionsMigratedIfIterateInstalled(self):
        self.qi.installProduct('plone.app.iterate')
        self.actions.object_buttons.iterate_checkin.permissions = (
            'Modify portal content',)
        three1_beta1(self.portal)
        self.failUnlessEqual(
            self.actions.object_buttons.iterate_checkin.permissions,
            ('iterate : Check in content',))

    def testIterateInstalledButActionMissing(self):
        self.qi.installProduct('plone.app.iterate')
        self.actions.object_buttons.manage_delObjects(['iterate_checkin'])
        three1_beta1(self.portal)
        self.failIf('iterate_checkin' in
                    self.actions.object_buttons.objectIds())

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestMigrations_v3_2))
    return suite
