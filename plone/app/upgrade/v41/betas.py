from BTrees.IIBTree import IISet
from BTrees.IIBTree import IITreeSet
from Products.CMFCore.utils import getToolByName
from Products.PluginIndexes.DateRangeIndex.DateRangeIndex import DateRangeIndex
from Products.PluginIndexes.FieldIndex.FieldIndex import FieldIndex
from Products.PluginIndexes.KeywordIndex.KeywordIndex import KeywordIndex
import transaction

from plone.app.upgrade.utils import loadMigrationProfile


def optimize_indexes(context):
    catalog = getToolByName(context, 'portal_catalog')
    for index in catalog.getIndexObjects():
        if isinstance(index, DateRangeIndex):
            # migrate internal IISet to IITreeSet
            for name in ('_since', '_since_only', '_until', '_until_only'):
                tree = getattr(index, name, None)
                if tree is not None:
                    for k, v in tree.items():
                        if isinstance(v, IISet):
                            tree[k] = IITreeSet(v)
                    transaction.savepoint(optimistic=True)
        elif isinstance(index, (FieldIndex, KeywordIndex)):
            # avoid using a simple int and always use a treeset instead to
            # allow conflict resolution inside the treeset to happen
            _index = getattr(index, '_index', None)
            if _index is not None:
                for k, v in _index.items():
                    if isinstance(v, int):
                        _index[k] = IITreeSet((v, ))
                transaction.savepoint(optimistic=True)


def to41beta1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:to41beta1')
    optimize_indexes(context)
