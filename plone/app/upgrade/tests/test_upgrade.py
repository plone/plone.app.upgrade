from Products.CMFPlone.factory import _DEFAULT_PROFILE
from Products.CMFCore.utils import getToolByName
from plone.app.upgrade.utils import version_match
from plone.app.upgrade.tests.base import MigrationTest
import mock


class TestUpgrade(MigrationTest):

    def afterSetUp(self):
        self.setup = getToolByName(self.portal, "portal_setup")

    def testListUpgradeSteps(self):
        # There should be no upgrade steps from the current version
        upgrades = self.setup.listUpgrades(_DEFAULT_PROFILE)
        self.assertEqual(len(upgrades), 0)

    def testProfileVersion(self):
        # The profile version for the base profile should be the same
        # as the file system version and the instance version
        self.setup = getToolByName(self.portal, 'portal_setup')

        current = self.setup.getVersionForProfile(_DEFAULT_PROFILE)
        current = tuple(current.split('.'))
        last = self.setup.getLastVersionForProfile(_DEFAULT_PROFILE)
        self.assertEqual(last, current)

    @mock.patch('plone.app.upgrade.utils.plone_version', '5.0b1')
    def testVersionMatch(self):
        self.assertFalse(version_match('2.5'))
        self.assertFalse(version_match('3.1b1'))
        self.assertFalse(version_match('5.2.b1'))
        self.assertTrue(version_match('5.0a3.dev0'))
        self.assertTrue(version_match('5.0b1.dev0'))
        self.assertTrue(version_match('5.0b3'))
        self.assertTrue(version_match('5.0'))

    def testDoUpgrades(self):
        self.setRoles(['Manager'])

        self.setup.setLastVersionForProfile(_DEFAULT_PROFILE, '2.5')
        upgrades = self.setup.listUpgrades(_DEFAULT_PROFILE)
        self.assertTrue(len(upgrades) > 0)

        request = self.portal.REQUEST
        request.form['profile_id'] = _DEFAULT_PROFILE

        steps = []
        for u in upgrades:
            if isinstance(u, list):
                steps.extend([s['id'] for s in u])
            else:
                steps.append(u['id'])

        request.form['upgrades'] = steps
        self.setup.manage_doUpgrades(request=request)

        # And we have reached our current profile version
        current = self.setup.getVersionForProfile(_DEFAULT_PROFILE)
        current = tuple(current.split('.'))
        last = self.setup.getLastVersionForProfile(_DEFAULT_PROFILE)
        self.assertEqual(last, current)

        # There are no more upgrade steps available
        upgrades = self.setup.listUpgrades(_DEFAULT_PROFILE)
        self.assertEqual(len(upgrades), 0)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestUpgrade))
    return suite
