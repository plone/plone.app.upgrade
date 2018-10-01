# -*- coding: utf-8 -*-
from Acquisition import aq_base
from Acquisition import aq_parent
from plone.app.theming.interfaces import IThemeSettings
from plone.app.upgrade.utils import get_property
from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.v40.alphas import cleanUpToolRegistry
from plone.app.vocabularies.types import BAD_TYPES
from plone.keyring.interfaces import IKeyManager
from plone.keyring.keymanager import KeyManager
from plone.keyring.keyring import Keyring
from plone.protect.interfaces import IDisableCSRFProtection
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IEditingSchema
from Products.CMFPlone.interfaces import IMaintenanceSchema
from Products.CMFPlone.interfaces import INavigationSchema
from Products.CMFPlone.interfaces import ISearchSchema
from Products.CMFPlone.interfaces import ISiteSchema
from Products.CMFPlone.utils import safe_unicode
from zope.component import getSiteManager
from zope.component import getUtility
from zope.component.hooks import getSite
from zope.globalrequest import getRequest
from zope.interface import alsoProvides
from zope.schema.interfaces import ConstraintNotSatisfied

import logging
import pkg_resources


try:
    pkg_resources.get_distribution('plone.app.caching')
except pkg_resources.DistributionNotFound:
    HAS_CACHING = False
else:
    HAS_CACHING = True
    from plone.app.caching.interfaces import IPloneCacheSettings

logger = logging.getLogger('plone.app.upgrade')

TOOLS_TO_REMOVE = ['portal_actionicons',
                   'portal_calendar',
                   'portal_interface',
                   'portal_discussion',
                   'portal_undo']


def to50alpha3(context):
    """5001 -> 5.0alpha3"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v50:to50alpha3')


def to50alpha1(context):
    """4.3 -> 5.0alpha1"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v50:to50alpha1')
    portal = getToolByName(context, 'portal_url').getPortalObject()

    # remove obsolete tools
    tools = [t for t in TOOLS_TO_REMOVE if t in portal]
    if tools:
        portal.manage_delObjects(tools)

    cleanUpToolRegistry(context)

    # migrate properties to portal_registry
    migrate_registry_settings(portal)

    # install plone.app.event
    try:
        from Products.CMFPlone.utils import get_installer
    except ImportError:
        # BBB For Plone 5.0 and lower.
        qi = getToolByName(portal, 'portal_quickinstaller')
    else:
        qi = get_installer(portal)
    if not qi.isProductInstalled('plone.resource'):
        qi.installProduct('plone.resource')
    if not qi.isProductInstalled('plone.app.event'):
        qi.installProduct('plone.app.event')

    # update the default view of the Members folder
    migrate_members_default_view(portal)

    # install the Barceloneta theme
    if portal.portal_skins.getDefaultSkin() == 'Sunburst Theme':
        if not qi.isProductInstalled('plonetheme.barceloneta'):
            qi.installProduct('plonetheme.barceloneta')

    upgrade_keyring(context)
    installOrUpgradePloneAppTheming(context)
    installOrUpgradePloneAppCaching(context)


def installOrUpgradePloneAppTheming(context):
    """Install plone.app.theming if not installed yet.

    Upgrade it for good measure if it is already installed.
    """
    profile_id = 'profile-plone.app.theming:default'
    portal_setup = getToolByName(context, 'portal_setup')
    registry = getUtility(IRegistry)
    try:
        registry.forInterface(IThemeSettings)
    except KeyError:
        # plone.app.theming not yet installed
        portal_setup.runAllImportStepsFromProfile(profile_id)
    else:
        # Might as well upgrade it if needed.
        portal_setup.upgradeProfile(profile_id)


def installOrUpgradePloneAppCaching(context):
    """Install plone.app.caching if not installed yet.

    Plone 5.0 installs it by default,
    and hides it from the add-ons control panel.

    Upgrade it for good measure if it is already installed.

    Note: plone.app.caching is required by Plone, not by
    Products.CMFPlone, so it may not be available.
    """
    if not HAS_CACHING:
        return
    profile_id = 'profile-plone.app.caching:default'
    portal_setup = getToolByName(context, 'portal_setup')
    if not portal_setup.profileExists(profile_id):
        # During tests, the package may be there, but the zcml may not have
        # been loaded, so the profile is not available.
        return
    registry = getUtility(IRegistry)
    try:
        registry.forInterface(IPloneCacheSettings)
    except KeyError:
        # plone.app.caching not yet installed
        portal_setup.runAllImportStepsFromProfile(profile_id)
    else:
        # Might as well upgrade it if needed.
        portal_setup.upgradeProfile(profile_id)


def lowercase_email_login(context):
    """If email is used as login name, lowercase the login names.
    """
    ptool = getToolByName(context, 'portal_properties')
    if ptool.site_properties.getProperty('use_email_as_login'):
        # We want the login name to be lowercase here.  This is new in PAS.
        logger.info('Email is used as login, setting PAS login_transform to '
                    "'lower'.")
        # This can take a while for large sites, as it automatically
        # transforms existing login names to lowercase.  It will fail
        # if this would result in non-unique login names.
        pas = getToolByName(context, 'acl_users')
        pas.manage_changeProperties(login_transform='lower')


def migrate_registry_settings(portal):
    site_props = portal.portal_properties.site_properties
    registry = portal.portal_registry
    portal_types = portal.portal_types
    registry['plone.site_title'] = safe_unicode(portal.title)
    if site_props.hasProperty('webstats_js'):
        registry['plone.webstats_js'] = safe_unicode(site_props.webstats_js)
    if site_props.hasProperty('enable_sitemap'):
        registry['plone.enable_sitemap'] = site_props.enable_sitemap

    if site_props.hasProperty('exposeDCMetaTags'):
        registry['plone.exposeDCMetaTags'] = site_props.exposeDCMetaTags
    if site_props.hasProperty('enable_livesearch'):
        registry['plone.enable_livesearch'] = site_props.enable_livesearch
    if site_props.hasProperty('types_not_searched'):
        registry['plone.types_not_searched'] = tuple(
            t for t in site_props.types_not_searched if t in portal_types)

    # Migrate first weekday setting
    # First, look, if plone.app.event < 2.0 was already installed.
    first_weekday = registry.get('plone.app.event.first_weekday', None)
    if first_weekday is None:
        # Try to get the value from portal_calendar, if available.
        portal_calendar = getattr(portal, 'portal_calendar', None)
        first_weekday = getattr(portal_calendar, 'firstweekday', None)


def migrate_members_default_view(portal):
    members = portal.get('Members')
    if members is None:
        return
    if 'index_html' in members:
        del members['index_html']
    members.layout = '@@member-search'


def upgrade_keyring(context):
    logger.info('upgrading keyring')
    manager = getUtility(IKeyManager)

    manager[u'_system'].fill()

    if u'_anon' not in manager:
        manager[u'_anon'] = Keyring()
    manager[u'_anon'].fill()

    if u'_forms' not in manager:
        manager[u'_forms'] = Keyring()
    manager[u'_forms'].fill()

    logger.info('add keyring to zope root if not done already')
    app = aq_parent(getSite())
    sm = getSiteManager(app)

    if sm.queryUtility(IKeyManager) is None:
        obj = KeyManager()
        sm.registerUtility(aq_base(obj), IKeyManager, '')

    # disable CSRF protection which will fail due to
    # using different secrets than when the authenticator
    # was generated
    request = getRequest()
    if request is not None:
        alsoProvides(request, IDisableCSRFProtection)


def to50alhpa3(context):
    """5.0alpha2 - > 5.0alpha3"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v50:to50alpha3')

    portal = getToolByName(context, 'portal_url').getPortalObject()
    registry = portal.portal_registry
    # At alpha3 we have the registry entry so we can migrate here
    first_weekday = registry.get('plone.app.event.first_weekday', None)
    if first_weekday is not None:
        # Set it. Otherwise, let plone.app.event install routine set it.
        registry['plone.first_weekday'] = first_weekday


def upgrade_editing_controlpanel_settings(context):
    """Copy editing control panel settings from portal properties into the new
       registry.
    """
    # get the old site properties
    portal_properties = getToolByName(context, 'portal_properties')
    site_properties = portal_properties.site_properties
    # get the new registry
    registry = getUtility(IRegistry)
    settings = registry.forInterface(
        IEditingSchema,
        prefix='plone',
    )
    # migrate the old site properties to the new registry
    if site_properties.hasProperty('visible_ids'):
        settings.visible_ids = site_properties.visible_ids
    if site_properties.hasProperty('enable_link_integrity_checks'):
        settings.enable_link_integrity_checks = \
            site_properties.enable_link_integrity_checks
    if site_properties.hasProperty('ext_editor'):
        settings.ext_editor = site_properties.ext_editor
    # settings.available_editors = site_properties.available_editors

    # Kupu will not be available as editor in Plone 5. Therefore we just
    # ignore the setting.  But there may be others (like an empty string)
    # that will give an error too.  So we validate the value.
    try:
        IEditingSchema['default_editor'].validate(
            site_properties.default_editor)
    except ConstraintNotSatisfied:
        logger.warning(
            'Ignoring invalid site_properties.default_editor %r.',
            site_properties.default_editor)
    except AttributeError:
        logger.warning(
            'Ignoring non existing attribute site_properties.default_editor.')
    else:
        settings.default_editor = site_properties.default_editor
    settings.lock_on_ttw_edit = get_property(
        site_properties,
        'lock_on_ttw_edit',
        None,
    )


def upgrade_maintenance_controlpanel_settings(context):
    """Copy maintenance control panel settings from portal properties into the
       new registry.
    """
    # get the old site properties
    portal_properties = getToolByName(context, 'portal_properties')
    site_properties = portal_properties.site_properties
    # get the new registry
    registry = getUtility(IRegistry)
    settings = registry.forInterface(
        IMaintenanceSchema,
        prefix='plone',
    )
    settings.days = get_property(
        site_properties,
        'number_of_days_to_keep',
        None,
    )


def upgrade_navigation_controlpanel_settings(context):
    """Copy navigation control panel settings from portal properties into the
       new registry.
    """
    # get the old site properties
    portal_properties = getToolByName(context, 'portal_properties')
    site_properties = portal_properties.site_properties
    navigation_properties = portal_properties.navtree_properties
    types_tool = getToolByName(context, 'portal_types')
    # get the new registry
    registry = getUtility(IRegistry)
    settings = registry.forInterface(
        INavigationSchema,
        prefix='plone',
    )
    settings.disable_folder_sections = site_properties.getProperty(
        'disable_folder_sections')
    settings.disable_nonfolderish_sections = site_properties.getProperty(
        'disable_nonfolderish_sections')
    settings.show_all_parents = navigation_properties.getProperty(
        'showAllParents')
    allTypes = types_tool.listContentTypes()
    blacklist = get_property(
        navigation_properties,
        'metaTypesNotToList',
        default_value=[],
    )
    settings.displayed_types = tuple([
        t for t in allTypes if t not in blacklist
        and t not in BAD_TYPES
    ])

    settings.enable_wf_state_filtering = navigation_properties.getProperty(
        'enable_wf_state_filtering')
    settings.wf_states_to_show = navigation_properties.getProperty(
        'wf_states_to_show')


def upgrade_search_controlpanel_settings(context):
    """Copy search control panel settings from portal properties into the
       new registry.
    """
    # get the old site properties
    portal_properties = getToolByName(context, 'portal_properties')
    site_properties = portal_properties.site_properties
    types_tool = getToolByName(context, 'portal_types')
    # get the new registry
    registry = getUtility(IRegistry)
    settings = registry.forInterface(
        ISearchSchema,
        prefix='plone',
    )

    if site_properties.hasProperty('enable_livesearch'):
        settings.enable_livesearch = site_properties.enable_livesearch
    types_not_searched = get_property(
        site_properties,
        'types_not_searched',
        default_value=[],
    )
    settings.types_not_searched = tuple([
        t for t in types_tool.listContentTypes()
        if t in types_not_searched and
        t not in BAD_TYPES
    ])


def upgrade_site_controlpanel_settings(context):
    """Copy site control panel settings from portal properties into the
       new registry.
    """
    # get the old site properties
    portal_properties = getToolByName(context, 'portal_properties')
    site_properties = portal_properties.site_properties
    portal = getSite()
    # get the new registry
    registry = getUtility(IRegistry)
    settings = registry.forInterface(
        ISiteSchema,
        prefix='plone',
    )
    settings.site_title = safe_unicode(portal.title)
    webstat_js = get_property(site_properties, 'webstats_js', '')
    settings.webstats_js = safe_unicode(webstat_js)
    settings.enable_sitemap = get_property(site_properties, 'enable_sitemap')
    if site_properties.hasProperty('exposeDCMetaTags'):
        settings.exposeDCMetaTags = site_properties.exposeDCMetaTags
