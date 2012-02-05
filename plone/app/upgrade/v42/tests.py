import unittest
from plone.app.upgrade.tests.base import FunctionalUpgradeTestCase
from Products.CMFCore.utils import getToolByName
from plone.app.upgrade.tests.base import MigrationTest
from plone.app.upgrade.utils import loadMigrationProfile


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



class TestMigrations_v4_2beta1(MigrationTest):

    profile = 'profile-plone.app.upgrade.v42:to42beta1'

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.failUnless(True)

    def testAddSiteAdminToKeywordRoles(self):
        ptool = self.portal.portal_properties
        site_props = ptool.site_properties
        site_props.allowRolesToAddKeywords = ('Manager', 'Reviewer')
        loadMigrationProfile(self.portal, self.profile)
        roles = site_props.allowRolesToAddKeywords
        self.assertEqual(roles, ('Manager', 'Reviewer', 'Site Administrator'))