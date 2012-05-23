import unittest
from Products.CMFCore.utils import getToolByName
from plone.app.upgrade.tests.base import MigrationTest
from plone.app.upgrade.utils import loadMigrationProfile


class TestMigrations_v4_3aplha1(MigrationTest):

    profile = 'profile-plone.app.upgrade.v43:to43alpha1'

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.failUnless(True)

    def testAddDisplayPublicationDateInBylineProperty(self):
        pprop = getToolByName(self.portal, 'portal_properties')
        self.assertEquals(
            pprop.site_properties.getProperty('displayPublicationDateInByline'),
            False)
