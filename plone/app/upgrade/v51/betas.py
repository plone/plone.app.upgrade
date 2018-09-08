# -*- coding: utf-8 -*-
from plone.app.upgrade.utils import cleanUpSkinsTool
from plone.app.upgrade.utils import loadMigrationProfile
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IFilterSchema
from Products.CMFPlone.interfaces import ISearchSchema
from Products.ZCatalog.ProgressHandler import ZLogHandler
from zExceptions import NotFound
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
    portal_properties = getToolByName(context, 'portal_properties')
    site_properties = portal_properties.site_properties
    # get the new registry
    registry = getUtility(IRegistry)
    settings = registry.forInterface(
        ISearchSchema,
        prefix='plone',
    )
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
    text = 'object/{0}'.format(script_name)
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
    results = zcatalog.unrestrictedSearchResults(object_provides=ifaces)
    num_objects = len(results)
    pghandler = ZLogHandler(1000)
    pghandler.init('Updating mime_type metadata', num_objects)
    for brain in results:
        pghandler.report(cnt)
        try:
            obj = brain._unrestrictedGetObject()
        except (AttributeError, KeyError, TypeError, NotFound):
            continue
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
    pghandler.finish()
    logger.info('Reindexed `mime_type` for %s items', str(cnt))


def move_safe_html_settings_to_registry(context):
    """ Move safe_html settings from portal_transforms to Plone registry.
    """
    registry = getUtility(IRegistry)
    try:
        settings = registry.forInterface(IFilterSchema, prefix='plone')
    except KeyError:
        # Catch case where valid_tags is not yet registered
        registry.registerInterface(IFilterSchema, prefix='plone')
        settings = registry.forInterface(IFilterSchema, prefix='plone')
    pt = getToolByName(context, 'portal_transforms')
    disable_filtering = pt.safe_html._config.get('disable_transform')
    raw_valid_tags = pt.safe_html._config.get('valid_tags') or {}
    raw_nasty_tags = pt.safe_html._config.get('nasty_tags') or {}
    valid_tags = [tag.decode() for tag in raw_valid_tags]
    nasty_tags = [tag.decode() for tag in raw_nasty_tags]
    settings.disable_filtering = disable_filtering
    settings.valid_tags = sorted(valid_tags)
    settings.nasty_tags = sorted(nasty_tags)


def remove_duplicate_iterate_settings(context):
    """When migrating from Plone 5 to 5.1 there might be
    duplicate settings for plone.app.iterate in the registry.
    One with the prefix 'plone' and one without.

    See https://github.com/plone/plone.app.iterate/pull/47
    """
    registry = getUtility(IRegistry)
    from plone.app.iterate.interfaces import IIterateSettings
    try:
        if 'plone.checkout_workflow_policy' in registry.records:
            del registry.records['plone.checkout_workflow_policy']
        if 'plone.enable_checkout_workflow' in registry.records:
            del registry.records['plone.enable_checkout_workflow']
    except KeyError:
        pass
    # Make sure the correct settings are actually initialized
    from Products.CMFPlone.utils import get_installer
    qi = get_installer(context)
    if qi.is_product_installed('plone.app.iterate'):
        registry.registerInterface(IIterateSettings)


def cleanup_import_steps(context):
    """Remove registration of old GS-import_steps since they were transformed
    into post_handlers. Otherwise the registered methods would run for each
    profile.
    See https://github.com/plone/Products.CMFPlone/issues/2238
    """
    steps = [
        'plone.app.contenttypes--plone-content',
        'plone.app.contenttypes',
    ]
    for step in steps:
        if step in context._import_registry.listSteps():
            context._import_registry.unregisterStep(step)
