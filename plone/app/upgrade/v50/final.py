# -*- coding: utf-8 -*-
from plone.app.upgrade.utils import loadMigrationProfile
from plone.dexterity.interfaces import IDexterityContent
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
            # check if there is a getIcon at all, this may not exist in some
            # customizations, who knows, but always exists in default Plone
            catalog.names.index('getIcon')
        except ValueError:
            logger.info('`getIcon` not in metadata, skip upgrade step')
            return
        cnt = 0
        # search whole catalog
        for brain in zcatalog.unrestrictedSearchResults():
            # create and apply metadata
            catalog.data[brain.getRID()] = catalog.recordify(
                # wake up object
                brain._unrestrictedGetObject()
            )
            cnt += 1  # we are curious
        # done
        logger.info('Reindexed `getIcon` for %s items' % str(cnt))

    refresh_getIcon_catalog_metadata(context)