# -*- coding: utf-8 -*-
from Acquisition import aq_base
from plone.app.upgrade.utils import loadMigrationProfile
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from zope.component import getUtility
from zope.component.hooks import getSite

import logging


logger = logging.getLogger('plone.app.upgrade')


def to500(context):
    """5.0rc3 -> 5.0.0"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v50:to500')
    portal = getSite()

    pprop = getToolByName(portal, 'portal_properties')
    site_properties = pprop['site_properties']
    registry = getUtility(IRegistry)

    def _migrate_list(original_id, new_id=None):
        if new_id is None:
            new_id = original_id
        if site_properties.hasProperty(original_id):
            value = site_properties.getProperty(original_id)
            value = [safe_unicode(a) for a in value]
            registry['plone.%s' % new_id] = value
            site_properties._delProperty(original_id)

    # Old versions of to50rc3 migrated values from
    # typesLinkToFolderContentsInFC which was wrong.
    # Here we do it again correctly.
    _migrate_list('typesUseViewActionInListings',
                  'types_use_view_action_in_listings')


def to501(context):
    """5.0 -> 5.0.1"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v50:to501')

    def refresh_getIcon_catalog_metadata(context):
        """
        get_icon redefined: now boolean:
        needs to update metadata
        true if item is type image or has image field (named 'image')
        e.g. leadimage
        see https://github.com/plone/Products.CMFPlone/issues/1226
        """
        # Attention, this relies heavily on catalog internals.

        # get the more visible zcatalog
        zcatalog = getToolByName(context, 'portal_catalog')

        # get the more hidden, inner (real) catalog implementation
        catalog = zcatalog._catalog
        try:
            # Get the getIcon index value and
            # check if there is a getIcon at all, this may not exist in some
            # customizations, who knows, but always exists in default Plone
            metadata_index = catalog.names.index('getIcon')
        except ValueError:
            logger.info('`getIcon` not in metadata, skip upgrade step')
            return

        cnt = 0
        # search whole catalog
        for brain in zcatalog.unrestrictedSearchResults():
            # First get the new value
            obj = brain._unrestrictedGetObject()
            new_value = bool(getattr(aq_base(obj), 'image', False))

            # We can now update the record with the new getIcon value
            record = list(catalog.data[brain.getRID()])
            record[metadata_index] = new_value
            catalog.data[brain.getRID()] = tuple(record)

            cnt += 1  # we are curious
        # done
        logger.info('Reindexed `getIcon` for %s items' % str(cnt))

    refresh_getIcon_catalog_metadata(context)


def to502(context):
    """5.0.1 -> 5.0.2"""

    # When migrating from Plone 4.3 to 5.0 the profile-version of
    # plone.app.querystring is 13 at this point but the upgrade-step
    # upgrade_to_5 has not been run. Let's run it.
    loadMigrationProfile(context, 'profile-plone.app.querystring:upgrade_to_5')


def to503(context):
    """5.0.2 -> 5.0.3"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v50:to503')


def to507(context):
    """5.0.6 -> 5.0.7"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v50:to507')


def to509(context):
    """5.0.8 -> 5.0.9"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v50:to509')


def fix_double_smaxage(context):
    """Fix caching definition.

    plone.resource.maxage has title and description from shared maxage.
    See https://github.com/plone/Products.CMFPlone/issues/1989
    """
    from plone.registry.interfaces import IPersistentField
    from plone.registry.record import Record
    from plone.registry import field
    from plone.registry import FieldRef
    from zope.component import queryAdapter
    registry = getUtility(IRegistry)
    # If these three registry records are not defined,
    # we do no fix.
    maxage = 'plone.app.caching.strongCaching.plone.resource.maxage'
    def_maxage = 'plone.app.caching.strongCaching.maxage'
    def_smaxage = 'plone.app.caching.strongCaching.smaxage'
    for name in (maxage, def_maxage, def_smaxage):
        if name not in registry:
            return
    if registry.records[maxage].field.recordName != def_smaxage:
        # no fix needed
        return
    field_ref = FieldRef(def_maxage, registry.records[def_maxage].field)
    old_value = registry[maxage]
    registry.records[maxage] = Record(field_ref, old_value)
    logger.info('Fixed {} to refer to {}.'.format(maxage, def_maxage))
