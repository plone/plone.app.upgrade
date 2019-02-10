# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.v40.alphas import cleanUpToolRegistry

import logging


logger = logging.getLogger('plone.app.upgrade')


def add_exclude_from_nav_index(context):
    """Add exclude_from_nav index to the portal_catalog.
    """
    name = 'exclude_from_nav'
    meta_type = 'BooleanIndex'
    catalog = getToolByName(context, 'portal_catalog')
    indexes = catalog.indexes()
    indexables = []
    if name not in indexes:
        catalog.addIndex(name, meta_type)
        indexables.append(name)
        logger.info('Added %s for field %s.', meta_type, name)
    if len(indexables) > 0:
        logger.info('Indexing new indexes %s.', ', '.join(indexables))
        catalog.manage_reindexIndex(ids=indexables)


def remove_legacy_resource_registries(context):
    """Remove portal_css and portal_javascripts."""
    portal_url = getToolByName(context, 'portal_url')
    portal = portal_url.getPortalObject()

    tools_to_remove = [
        'portal_css',
        'portal_javascripts',
    ]

    # remove obsolete tools
    tools = [t for t in tools_to_remove if t in portal]
    if tools:
        portal.manage_delObjects(tools)

    cleanUpToolRegistry(context)


def to52beta1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v52:to52beta1')
    add_exclude_from_nav_index(context)
    remove_legacy_resource_registries(context)
