# -*- coding: utf-8 -*-
from plone.app.upgrade.utils import loadMigrationProfile
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import ISearchSchema
from zope.component import getUtility

import logging


logger = logging.getLogger('plone.app.upgrade')


def to51beta1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v51:to51beta1')


def addSortOnProperty(context):
    """Add sort_on field to search controlpanel.
    
    The default value of this field is relevance.
    """
    # get the old site properties
    portal_properties = getToolByName(context, "portal_properties")
    site_properties = portal_properties.site_properties
    # get the new registry
    registry = getUtility(IRegistry)
    # XXX: Somehow this code is executed for old migration steps as well
    # ( < Plone 4 ) and breaks because there is no registry. Looking up the
    # registry interfaces with 'check=False' will not work, because it will
    # return a settings object and then fail when we try to access the
    # attributes.
    try:
        settings = registry.forInterface(
            ISearchSchema,
            prefix='plone',
        )
    except KeyError:
        settings = False
    if settings:
        # migrate the old site properties to the new registry
        if site_properties.hasProperty('sort_on'):
            settings.sort_on = site_properties.sort_on
        else:
            settings.sort_on = 'relevance'
        logger.log(logging.INFO,
                   "Added 'sort_on' property to site_properties.")
