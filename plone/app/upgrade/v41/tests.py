import unittest
from plone.app.upgrade.tests.base import FunctionalUpgradeTestCase
from Products.ZCatalog.ZCatalog import ZCatalog
from Products.ZCTextIndex.ZCTextIndex import ZCTextIndex, PLexicon
from Products.ZCTextIndex.OkapiIndex import OkapiIndex


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


class MigrationUnitTests(unittest.TestCase):

    def test_fixOkapiIndexes(self):
        catalog = ZCatalog('catalog')
        catalog.lexicon = PLexicon('lexicon')
        catalog.addIndex('test',
            ZCTextIndex('test', index_factory=OkapiIndex,
                        caller=catalog, lexicon_id='lexicon'))
        catalog.Indexes['test'].index._totaldoclen = -1000

        from plone.app.upgrade.v41.final import fixOkapiIndexes
        fixOkapiIndexes(catalog)
        self.assertEqual(0L, catalog.Indexes['test'].index._totaldoclen())
