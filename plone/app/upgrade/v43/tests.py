from plone.app.upgrade.tests.base import MigrationTest
from plone.app.upgrade.utils import loadMigrationProfile

import alphas


class TestMigrations_v4_3alpha1(MigrationTest):

    profile = 'profile-plone.app.upgrade.v43:upgradeToI18NCaseNormalizer'

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.failUnless(True)

    def testUpgradeToI18NCaseNormalizer(self):
        ctool = self.portal.portal_catalog
        self.assertEqual(ctool.plone_lexicon._pipeline[1].__class__.__name__, 'CaseNormalizer')
        alphas.upgradeToI18NCaseNormalizer(self.portal.portal_setup)
        self.assertEqual(ctool.plone_lexicon._pipeline[1].__class__.__name__, 'I18NNormalizer')
        self.failUnless(len(ctool.searchResults(SearchableText="welcome")) > 0)
