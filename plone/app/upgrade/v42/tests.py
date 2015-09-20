# -*- coding: utf-8 -*-
from plone.app.upgrade.tests.base import MigrationTest
from plone.app.upgrade.utils import loadMigrationProfile
import betas


class TestMigrations_v4_2beta1(MigrationTest):

    profile = 'profile-plone.app.upgrade.v42:to42beta1'

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.assertTrue(True)

    def testAddSiteAdminToKeywordRoles(self):
        ptool = self.portal.portal_properties
        site_props = ptool.site_properties
        if not site_props.hasProperty('allowRolesToAddKeywords'):
            return
        site_props.allowRolesToAddKeywords = ('Manager', 'Reviewer')
        loadMigrationProfile(self.portal, self.profile)
        betas.to42beta1(self.portal.portal_setup)
        roles = site_props.allowRolesToAddKeywords
        self.assertEqual(roles, ('Manager', 'Reviewer', 'Site Administrator'))
