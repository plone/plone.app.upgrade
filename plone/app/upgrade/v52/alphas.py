# -*- coding: utf-8 -*-
from plone.app.upgrade.utils import cleanUpSkinsTool
from plone.app.upgrade.utils import loadMigrationProfile
from plone.folder.nogopip import manage_addGopipIndex
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility

import logging


logger = logging.getLogger('plone.app.upgrade')


def cleanup_resources():
    registry = getUtility(IRegistry)
    record = 'plone.bundles/plone-legacy.resources'
    resources = registry.records[record]

    if u'jquery-highlightsearchterms' in resources.value:
        resources.value.remove(u'jquery-highlightsearchterms')


def migrate_gopipindex(context):
    # GopipIndex class has moved from p.a.folder to p.folder
    # just remove and reinstall the index
    catalog = getToolByName(context, 'portal_catalog')
    catalog.manage_delIndex('getObjPositionInParent')
    manage_addGopipIndex(catalog, 'getObjPositionInParent')


def add_exclude_from_nav_index(context):
    """Add exclude_from_nav index to the portal_catalog.
    """
    name = 'exclude_from_nav'
    meta_type = 'BooleanIndex'
    catalog = getToolByName(context, 'portal_catalog')
    indexes = catalog.indexes()
    indexables = []
    if 'name' not in indexes:
        catalog.addIndex(name, meta_type)
        indexables.append(name)
        logger.info('Added %s for field %s.', meta_type, name)
    if len(indexables) > 0:
        logger.info('Indexing new indexes %s.', ', '.join(indexables))
        catalog.manage_reindexIndex(ids=indexables)


def to52alpha1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v52:to52alpha1')
    portal = getToolByName(context, 'portal_url').getPortalObject()
    cleanUpSkinsTool(portal)

    cleanup_resources()
    migrate_gopipindex(context)
    add_exclude_from_nav_index(context)


def to52alpha2(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v52:to52alpha2')
