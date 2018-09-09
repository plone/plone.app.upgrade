# -*- coding: utf-8 -*-
from plone.app.upgrade.utils import cleanUpSkinsTool
from plone.app.upgrade.utils import loadMigrationProfile
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility

import logging


logger = logging.getLogger('plone.app.upgrade')


def to52alpha1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v52:to52alpha1')
    portal = getToolByName(context, 'portal_url').getPortalObject()
    cleanUpSkinsTool(portal)

    registry = getUtility(IRegistry)
    record = 'plone.bundles/plone-legacy.resources'
    resources = registry.records[record]
    if u'jquery-highlightsearchterms' in resources.value:
        resources.value.remove(u'jquery-highlightsearchterms')
