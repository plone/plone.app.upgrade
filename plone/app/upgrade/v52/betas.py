# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from plone.app.upgrade.utils import loadMigrationProfile
from zc.relation.interfaces import ICatalog
from zope import component
from zope.intid.interfaces import IntIdMissingError


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


def remove_interface_indexes_from_relations_catalog():
    """ remove unused interface indexes from relations catalog """
    catalog = component.queryUtility(ICatalog)
    indexes_to_remove = [
        'from_interfaces_flattened',
        'to_interfaces_flattened'
    ]
    for index_to_remove in indexes_to_remove:
        if index_to_remove in catalog._name_TO_mapping:
            catalog.removeValueIndex(index_to_remove)

    for rel in catalog:
        catalog.unindex(rel)
        try:
            catalog.index(rel)
        except IntIdMissingError:
            logger.warn('Broken relation removed.')


def to52beta1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v52:to52beta1')
    add_exclude_from_nav_index(context)
    remove_interface_indexes_from_relations_catalog()
