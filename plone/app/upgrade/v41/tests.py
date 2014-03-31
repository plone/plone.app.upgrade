import unittest
from Products.ZCatalog.ZCatalog import ZCatalog
from Products.ZCTextIndex.ZCTextIndex import ZCTextIndex, PLexicon
from Products.ZCTextIndex.OkapiIndex import OkapiIndex


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
