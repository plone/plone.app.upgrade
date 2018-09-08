# -*- coding: utf-8 -*-
from plone.app.upgrade.utils import cleanUpSkinsTool
from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.v40.alphas import cleanUpToolRegistry
from Products.CMFCore.utils import getToolByName

import logging


logger = logging.getLogger('plone.app.upgrade')


def to52alpha1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v52:to52alpha1')
    portal = getToolByName(context, 'portal_url').getPortalObject()
    cleanUpSkinsTool(portal)

def remove_portal_tools(context):
    """Remove some portal tools."""
    portal_url = getToolByName(context, 'portal_url')
    portal = portal_url.getPortalObject()

    tools_to_remove = [
        'portal_css',
        'portal_javascripts',
    ]

    # remove obsolete tools
    tools = [t for t in tools_to_remove if t in portal]
    portal.manage_delObjects(tools)

    cleanUpToolRegistry(context)
