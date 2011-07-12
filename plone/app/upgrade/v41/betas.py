import transaction
from Products.CMFCore.utils import getToolByName
from Products.PluginIndexes.BooleanIndex.BooleanIndex import BooleanIndex
from Products.PluginIndexes.DateRangeIndex.DateRangeIndex import DateRangeIndex
from BTrees.IIBTree import IISet
from BTrees.IIBTree import IITreeSet

from zope.event import notify
from zope.lifecycleevent import ObjectCreatedEvent

from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.utils import logger
from plone.app.upgrade.v40.betas import fix_cataloged_interface_names


def optimize_rangeindex_floor_ceiling(index):
    # respect the new ceiling and floor values
    logger.info('Optimizing range index `%s` to respect floor and ceiling '
        'dates' % index.getId())
    ceiling_value = index.ceiling_value
    floor_value = index.floor_value

    _insertForwardIndexEntry = index._insertForwardIndexEntry
    _removeForwardIndexEntry = index._removeForwardIndexEntry
    _unindex = index._unindex
    i = 0
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
            i += 1
            if i % 10000 == 0:
                logger.info('Processed %s items.' % i)
                transaction.savepoint(optimistic=True)

    transaction.savepoint(optimistic=True)
    logger.info('Finished range index optimization.')


def optimize_rangeindex_int_iiset(index):
    # migrate internal int and IISet to IITreeSet
    logger.info('Converting to IITreeSet for index `%s`.' % index.getId())
    for name in ('_since', '_since_only', '_until', '_until_only'):
        tree = getattr(index, name, None)
        if tree is not None:
            logger.info('Converting tree `%s`.' % name)
            i = 0
            for k, v in tree.items():
                if isinstance(v, IISet):
                    tree[k] = IITreeSet(v)
                    i += 1
                elif isinstance(v, int):
                    tree[k] = IITreeSet((v, ))
                    i += 1
                if i and i % 10000 == 0:
                    transaction.savepoint(optimistic=True)
                    logger.info('Processed %s items.' % i)

    transaction.savepoint(optimistic=True)
    logger.info('Finished conversion.')


def update_boolean_index(index):
    index_length = index._index_length
    if index_length is not None:
        return
    logger.info('Updating BooleanIndex `%s`.' % index.getId())
    index._inline_migration()
    logger.info('Updated BooleanIndex `%s`.' % index.getId())


def optimize_indexes(context):
    catalog = getToolByName(context, 'portal_catalog')
    for index in catalog.getIndexObjects():
        if isinstance(index, DateRangeIndex):
            optimize_rangeindex_floor_ceiling(index)
            optimize_rangeindex_int_iiset(index)
        elif isinstance(index, BooleanIndex):
            update_boolean_index(index)


def fix_uuids_topic_criteria(context):
    catalog = getToolByName(context, 'portal_catalog')
    search = catalog.unrestrictedSearchResults
    for brain in search(Type='Collection'):
        obj = brain.getObject()
        crits = [x for x in obj.contentValues() if x.getId().startswith('crit__')]
        for crit in crits:
            if getattr(crit, '_plone.uuid', None) is None:
                notify(ObjectCreatedEvent(crit))
    logger.info('Added missing UUIDs to topic-criteria')


def to41beta1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:to41beta1')


def to41beta2(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:to41beta2')


def to41rc1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:to41rc1')
    optimize_indexes(context)
    # run this again to make sure we respect the blacklist, in an upgrade from
    # Plone < 4 we do the work earlier, so we don't have to iterate twice over
    # the object_provides index
    fix_cataloged_interface_names(context)


def to41rc2(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:to41rc2')


def to41rc3(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:to41rc3')


def to41rc4(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:to41rc4')
    fix_uuids_topic_criteria(context)

def to41final(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:to41final')
