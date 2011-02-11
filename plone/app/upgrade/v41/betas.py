from BTrees.IIBTree import IIBTree
from BTrees.IIBTree import IISet
from BTrees.IIBTree import IITreeSet
from Products.CMFCore.utils import getToolByName
from Products.PluginIndexes.BooleanIndex.BooleanIndex import BooleanIndex
from Products.PluginIndexes.DateRangeIndex.DateRangeIndex import DateRangeIndex
from Products.PluginIndexes.FieldIndex.FieldIndex import FieldIndex
from Products.PluginIndexes.KeywordIndex.KeywordIndex import KeywordIndex
import transaction

from plone.app.upgrade.utils import loadMigrationProfile


def convert_to_booleanindex(index):
    if isinstance(index, BooleanIndex):
        return
    index.__class__ = BooleanIndex
    index._p_changed = True
    # convert _unindex from IOBTree to IIBTree
    old_unindex = index._unindex
    if not isinstance(old_unindex, IIBTree):
        index._unindex = _unindex = IIBTree()
        for k, v in old_unindex.items():
            # docid to value (True, False)
            _unindex[k] = int(bool(v))
        del old_unindex
        transaction.savepoint(optimistic=True)
    # convert _index from OOBTree to IITreeSet
    old_index = index._index
    if not isinstance(old_index, IITreeSet):
        index._index = _index = IITreeSet()
        for k, v in old_index.items():
            # value to docid (int or treeset)
            if bool(k):
                # only true values get into the new _index
                if isinstance(v, int):
                    _index.add(v)
                else:
                    _index.update(v)
        del old_index
        transaction.savepoint(optimistic=True)


def convert_to_uuidindex(index):
    pass


def optimize_rangeindex(index):
    # migrate internal IISet to IITreeSet
    for name in ('_since', '_since_only', '_until', '_until_only'):
        tree = getattr(index, name, None)
        if tree is not None:
            for k, v in tree.items():
                if isinstance(v, IISet):
                    tree[k] = IITreeSet(v)
            transaction.savepoint(optimistic=True)


def optimize_unindex(index):
    # avoid using a simple int and always use a treeset instead to
    # allow conflict resolution inside the treeset to happen
    _index = getattr(index, '_index', None)
    if _index is not None:
        for k, v in _index.items():
            if isinstance(v, int):
                _index[k] = IITreeSet((v, ))
        transaction.savepoint(optimistic=True)


def optimize_indexes(context):
    catalog = getToolByName(context, 'portal_catalog')
    for index in catalog.getIndexObjects():
        index_id = index.getId()
        if isinstance(index, DateRangeIndex):
            optimize_rangeindex(index)
        elif index_id in ('is_default_page', 'is_folderish'):
            convert_to_booleanindex(index)
        elif index_id == 'UID':
            convert_to_uuidindex(index)
        elif isinstance(index, (FieldIndex, KeywordIndex)):
            optimize_unindex(index)


def to41beta1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:to41beta1')
    optimize_indexes(context)
