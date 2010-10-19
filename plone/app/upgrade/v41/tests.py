from plone.app.upgrade.tests.base import FunctionalUpgradeTestCase

class TestFunctionalMigrations(FunctionalUpgradeTestCase):

    def testFullUpgrade(self):
        # this tests a full upgrade from a Plone 4.0 ZEXP
        self.importFile(__file__, 'test-full.zexp')
        oldsite, result = self.migrate()

        mig = oldsite.portal_migration
        self.failIf(mig.needUpgrading())

        diff = self.export()
        len_diff = len(diff.split('\n'))
        # self.failUnless(len_diff <= 2700)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestFunctionalMigrations))
    return suite
