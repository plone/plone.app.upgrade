import logging
import re

from Products.CMFCore.utils import getToolByName
from Products.ZCatalog.ProgressHandler import ZLogHandler

from plone.app.upgrade.utils import loadMigrationProfile

logger = logging.getLogger('plone.app.upgrade')
num_sort_regex = re.compile('\d+')


def reindex_sortable_title(context):
    from Products.CMFPlone.CatalogTool import MAX_SORTABLE_TITLE
    catalog = getToolByName(context, 'portal_catalog')
    _catalog = catalog._catalog
    indexes = _catalog.indexes
    sort_title_index = indexes.get('sortable_title', None)
    if sort_title_index is None:
        return
    from Products.PluginIndexes.FieldIndex import FieldIndex
    if not isinstance(sort_title_index, FieldIndex.FieldIndex):
        return
    change = []
    pghandler = ZLogHandler(10000)
    logger.info('Analyzing sortable_title index')
    pghandler.init('Analyzing sortable_title index', len(sort_title_index))
    for i, (name, rids) in enumerate(sort_title_index._index.iteritems()):
        pghandler.report(i)
        if len(name) > MAX_SORTABLE_TITLE or num_sort_regex.match(name):
            change.extend(list(rids.keys()))
    pghandler.finish()
    update_metadata = 'sortable_title' in _catalog.schema
    pghandler = ZLogHandler(1000)
    logger.info('Updating sortable_title index')
    pghandler.init('Updating sortable_title index', len(change))
    for i, rid in enumerate(change):
        pghandler.report(i)
        brain = _catalog[rid]
        try:
            obj = brain.getObject()
        except AttributeError:
            continue
        if update_metadata:
            obj.reindexObject()
        else:
            obj.reindexObject(idxs=['sortable_title'])
    pghandler.finish()
    logger.info('Updated `sortable_title` index.')


def to43alpha1(context):
    """4.2 -> 4.3alpha1
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v43:to43alpha1')
    reindex_sortable_title(context)
