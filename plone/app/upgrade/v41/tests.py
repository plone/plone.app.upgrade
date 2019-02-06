# -*- coding: utf-8 -*-
from Products.ZCatalog.ZCatalog import ZCatalog
from Products.ZCTextIndex.OkapiIndex import OkapiIndex
from Products.ZCTextIndex.ZCTextIndex import PLexicon
from Products.ZCTextIndex.ZCTextIndex import ZCTextIndex

import six
import unittest


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
        self.assertEqual(0, catalog.Indexes['test'].index._totaldoclen())


if not six.PY2:
    def test_suite():
        return unittest.TestSuite()
