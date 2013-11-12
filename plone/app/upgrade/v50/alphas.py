# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from plone.app.upgrade.utils import loadMigrationProfile
import logging

logger = logging.getLogger('plone.app.upgrade')

TOOLS_TO_REMOVE = ['portal_actionicons',
                   'portal_calendar',
                   'portal_interface',
                   'portal_discussion',
                   'portal_undo']


def to50alpha1(context):
    """4.3 -> 5.0alpha1"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v50:to50alpha1')

    # install plone.app.event
    portal = getToolByName(context, 'portal_url').getPortalObject()
    qi = getToolByName(portal, 'portal_quickinstaller')
    if not qi.isProductInstalled('plone.app.event'):
        qi.installProduct('plone.app.event')

    # migrate first weekday setting
    portal_calendar = getattr(portal, 'portal_calendar', None)
    if portal_calendar is not None:
        first_weekday = getattr(portal.portal_calendar, 'firstweekday', 0)
        portal.portal_registry['plone.app.event.first_weekday'] = first_weekday

    # remove obsolete tools
    tools = [t for t in TOOLS_TO_REMOVE if t in portal]
    portal.manage_delObjects(tools)


def lowercase_email_login(context):
    """If email is used as login name, lowercase the login names.
    """
    ptool = getToolByName(context, 'portal_properties')
    if ptool.site_properties.getProperty('use_email_as_login'):
        # We want the login name to be lowercase here.  This is new in PAS.
        logger.info("Email is used as login, setting PAS login_transform to "
                    "'lower'.")
        # This can take a while for large sites, as it automatically
        # transforms existing login names to lowercase.  It will fail
        # if this would result in non-unique login names.
        pas = getToolByName(context, 'acl_users')
        pas.manage_changeProperties(login_transform='lower')
