import unittest
from Products.CMFCore.utils import getToolByName
from plone.app.upgrade.tests.base import MigrationTest
from plone.app.upgrade.utils import loadMigrationProfile

import alphas


class TestMigrations_v4_3alpha1(MigrationTest):

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.failUnless(True)

    def testAddDisplayPublicationDateInBylineProperty(self):
        pprop = getToolByName(self.portal, 'portal_properties')
        self.assertEquals(
            pprop.site_properties.getProperty('displayPublicationDateInByline'),
            False)

    def testUpgradeToI18NCaseNormalizer(self):
        from Products.CMFPlone.UnicodeSplitter.splitter import Splitter, CaseNormalizer
        ctool = self.portal.portal_catalog
        ctool.plone_lexicon._pipeline[1] == (Splitter(), CaseNormalizer())
        alphas.upgradeToI18NCaseNormalizer(self.portal.portal_setup)
        self.assertEqual(ctool.plone_lexicon._pipeline[1].__class__.__name__, 'I18NNormalizer')
        self.failUnless(len(ctool.searchResults(SearchableText="welcome")) > 0)
