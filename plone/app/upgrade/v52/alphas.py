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


def to52alpha1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v52:to52alpha1')
    portal = getToolByName(context, 'portal_url').getPortalObject()
    cleanUpSkinsTool(portal)

    cleanup_resources()
    migrate_gopipindex(context)
