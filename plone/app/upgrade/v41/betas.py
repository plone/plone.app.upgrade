import transaction
from Products.CMFCore.utils import getToolByName
from Products.PluginIndexes.DateRangeIndex.DateRangeIndex import DateRangeIndex

from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.v40.betas import fix_cataloged_interface_names


def optimize_rangeindex(index):
    # respect the new ceiling and floor values
    ceiling_value = index.ceiling_value
    floor_value = index.floor_value

    _insertForwardIndexEntry = index._insertForwardIndexEntry
    _removeForwardIndexEntry = index._removeForwardIndexEntry
    _unindex = index._unindex
    for docid, datum in _unindex.iteritems():
        if datum == (None, None):
            continue
        since, until = datum
        changed = False
        if since is not None and since < floor_value:
            since = None
            changed = True
        if until is not None and until > ceiling_value:
            until = None
            changed = True
        if changed:
            _removeForwardIndexEntry(datum[0], datum[1], docid)
            _insertForwardIndexEntry(since, until, docid)
            # we only change the value and not the keys of the btree, so we
            # safely iterate over it while modifying it
            _unindex[docid] = (since, until)

    transaction.savepoint(optimistic=True)


def optimize_indexes(context):
    catalog = getToolByName(context, 'portal_catalog')
    for index in catalog.getIndexObjects():
        if isinstance(index, DateRangeIndex):
            optimize_rangeindex(index)


def to41beta1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:to41beta1')


def to41beta2(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:to41beta2')


def to41beta3(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:to41beta3')
    optimize_indexes(context)
    # run this again to make sure we respect the blacklist, in an upgrade from
    # Plone < 4 we do the work earlier, so we don't have to iterate twice over
    # the object_provides index
    fix_cataloged_interface_names(context)
