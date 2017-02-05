# -*- coding: utf-8 -*-
from plone.app.upgrade.utils import cleanUpSkinsTool
from plone.app.upgrade.utils import loadMigrationProfile
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import ISearchSchema
from zope.component import getUtility

import logging


logger = logging.getLogger('plone.app.upgrade')

_marker = dict()


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


def remove_leftover_skin_layers(context):
    """Products.MimetypesRegistry no longer has a skin layer, remove it.
    """
    cleanUpSkinsTool(context)


def remove_jquery_cookie_from_stub_js_modules(context):
    """Remove jquery.cookie from plone-logged-in bundle's stub_js_modules.
    The toolbar, which has a dependency on jquery.cookie, was moved from the
    plone bundle to plone-logged-in in CMPlone 5.1a2.
    """
    registry = getUtility(IRegistry)
    reg_key = 'plone.bundles/plone-logged-in.stub_js_modules'
    value = registry.get(reg_key, [])
    if 'jquery.cookie' in value:
        value.remove('jquery.cookie')
        registry[reg_key] = value


def move_pw_reset_tool(context):
    """ Move PasswordResetTool from its own product to CMFPlone
    """
    pw_reset_tool = getToolByName(context, 'portal_password_reset')
    # Need to use getattr here. The _timedelta and _check_user are a class
    # attributes and not available in the instance dict until set
    # in case of defaults the do not exist in the <persistent broken ...>
    # object we fetch here.
    old_days_timeout = getattr(pw_reset_tool, '_timedelta', _marker)
    old_user_check = getattr(pw_reset_tool, '_user_check', _marker)
    portal = getToolByName(context, 'portal_url').getPortalObject()
    del portal['portal_password_reset']
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v51:to51beta1')
    pw_reset_tool = getToolByName(context, 'portal_password_reset')
    if old_days_timeout is not _marker:
        if old_days_timeout < 1:
            old_days_timeout = 7
        pw_reset_tool._timedelta = int(old_days_timeout)
    if old_user_check is not _marker:
        pw_reset_tool._user_check = bool(old_user_check)


def remove_displayContentsTab_from_action_expressions(context):
    """Remove the displayContentsTab script from action expressions.

    This script was removed, but it can still be in actions,
    at least in portal_actions/object/folderContents,
    where it makes the homepage fail to load.
    """
    atool = getToolByName(context, 'portal_actions')
    actions = atool.listActions()
    if not actions:
        return []
    script_name = 'displayContentsTab'
    text = 'object/{}'.format(script_name)
    for ac in actions:
        if script_name not in ac.available_expr:
            continue
        path = '/'.join(ac.getPhysicalPath())
        if ac.available_expr.strip() == text:
            ac._setPropValue('available_expr', '')
            logger.info('Removed %s from action at %s', text, path)
            continue
        # The script is in the expression, but it is different than what
        # we expect.  We can only warn the user.
        logger.warn('Action at %s references removed script %s in available. '
                    'expression %r. Please change it',
                    path, text, ac.available_expr)
