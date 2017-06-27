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


def update_social_media_fields(context):
    """Update twitter_username, facebook_app_id and facebook_username
    field values as they are now declared as ASCIILine instead of
    TextLine.
    """
    twitter_username = ''
    facebook_app_id = ''
    facebook_username = ''
    from Products.CMFPlone.interfaces.controlpanel import ISocialMediaSchema
    registry = getUtility(IRegistry)
    settings = registry.forInterface(ISocialMediaSchema, prefix='plone')
    if settings.twitter_username:
        twitter_username = str(settings.twitter_username)
    if settings.facebook_app_id:
        facebook_app_id = str(settings.facebook_app_id)
    if settings.facebook_username:
        facebook_username = str(settings.facebook_username)
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v51:to51beta4')
    settings.twitter_username = twitter_username
    settings.facebook_app_id = facebook_app_id
    settings.facebook_username = facebook_username

    logger.log(logging.INFO, 'Field types updated on social media schema')


def reindex_mime_type(context):
    # Attention, this relies heavily on catalog internals.
    # get the more visible zcatalog
    zcatalog = getToolByName(context, 'portal_catalog')
    # get the more hidden, inner (real) catalog implementation
    catalog = zcatalog._catalog
    try:
        metadata_index = catalog.names.index('mime_type')
    except ValueError:
        logger.info('`mime_type` not in metadata, skip upgrade step')
        return
    # we are interested in dexterity and archtetype images and files:
    ifaces = ['plone.app.contenttypes.interfaces.IImage',
              'plone.app.contenttypes.interfaces.IFile',
              'Products.ATContentTypes.interfaces.file.IFileContent',
              'Products.ATContentTypes.interfaces.image.IImageContent']
    cnt = 0
    for brain in zcatalog.unrestrictedSearchResults(object_provides=ifaces):
        obj = brain._unrestrictedGetObject()
        if not obj:
            continue
        # First get the new value:
        new_value = ''
        try:  # Dexterity
            new_value = obj.content_type()
        except TypeError:  # Archetypes
            new_value = obj.content_type
        except AttributeError:
            continue
        # We can now update the record with the new mime_type value
        record = list(catalog.data[brain.getRID()])
        record[metadata_index] = new_value
        catalog.data[brain.getRID()] = tuple(record)
        cnt += 1
    logger.info('Reindexed `mime_type` for %s items' % str(cnt))
