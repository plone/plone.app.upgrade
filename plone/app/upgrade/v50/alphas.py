# -*- coding: utf-8 -*-
import logging

from Acquisition import aq_parent, aq_base
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IEditingSchema
from Products.CMFPlone.interfaces import IMaintenanceSchema
from Products.CMFPlone.interfaces import INavigationSchema
from Products.CMFPlone.interfaces import ISearchSchema
from Products.CMFPlone.interfaces import ISiteSchema
from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.v40.alphas import cleanUpToolRegistry
from plone.app.vocabularies.types import BAD_TYPES
from plone.keyring.interfaces import IKeyManager
from plone.keyring.keymanager import KeyManager
from plone.keyring.keyring import Keyring
from plone.registry.interfaces import IRegistry
from zope.component import getSiteManager
from zope.component import getUtility
from zope.component.hooks import getSite


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
    portal.manage_delObjects(tools)

    cleanUpToolRegistry(context)

    # migrate properties to portal_registry
    migrate_registry_settings(portal)

    # install plone.app.event
    qi = getToolByName(portal, 'portal_quickinstaller')
    if not qi.isProductInstalled('plone.app.event'):
        qi.installProduct('plone.app.event')

    # update the default view of the Members folder
    migrate_members_default_view(portal)

    # install the Barceloneta theme
    if portal.portal_skins.getDefaultSkin() == 'Sunburst Theme':
        if not qi.isProductInstalled('plonetheme.barceloneta'):
            qi.installProduct('plonetheme.barceloneta')

    upgrade_keyring(context)


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


def migrate_registry_settings(portal):
    site_props = portal.portal_properties.site_properties
    registry = portal.portal_registry
    portal_types = portal.portal_types
    registry['plone.site_title'] = portal.title.decode('utf8')
    registry['plone.webstats_js'] = site_props.webstats_js.decode('utf8')
    registry['plone.enable_sitemap'] = site_props.enable_sitemap

    if site_props.hasProperty('exposeDCMetaTags'):
        registry['plone.exposeDCMetaTags'] = site_props.exposeDCMetaTags
    if site_props.hasProperty('enable_livesearch'):
        registry['plone.enable_livesearch'] = site_props.enable_livesearch
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
            IEditingSchema,
            prefix='plone',
        )
    except KeyError:
        settings = False
    if settings:
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
        # ignore the setting.
        if site_properties.default_editor != 'Kupu':
            settings.default_editor = site_properties.default_editor
        settings.lock_on_ttw_edit = site_properties.lock_on_ttw_edit


def upgrade_maintenance_controlpanel_settings(context):
    """Copy maintenance control panel settings from portal properties into the
       new registry.
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
            IMaintenanceSchema,
            prefix='plone',
        )
    except KeyError:
        settings = False
    if settings:
        settings.days = site_properties.number_of_days_to_keep


def upgrade_navigation_controlpanel_settings(context):
    """Copy navigation control panel settings from portal properties into the
       new registry.
    """
    # get the old site properties
    portal_properties = getToolByName(context, "portal_properties")
    site_properties = portal_properties.site_properties
    navigation_properties = portal_properties.navtree_properties
    types_tool = getToolByName(context, "portal_types")
    # get the new registry
    registry = getUtility(IRegistry)
    # XXX: Somehow this code is executed for old migration steps as well
    # ( < Plone 4 ) and breaks because there is no registry. Looking up the
    # registry interfaces with 'check=False' will not work, because it will
    # return a settings object and then fail when we try to access the
    # attributes.
    try:
        settings = registry.forInterface(
            INavigationSchema,
            prefix='plone',
        )
    except KeyError:
        settings = False
    if settings:
        settings.disable_folder_sections = site_properties.getProperty(
            'disable_folder_sections')
        settings.disable_nonfolderish_sections = site_properties.getProperty(
            'disable_nonfolderish_sections')
        settings.show_all_parents = navigation_properties.getProperty(
            'showAllParents')
        allTypes = types_tool.listContentTypes()
        blacklist = navigation_properties.metaTypesNotToList
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
    portal_properties = getToolByName(context, "portal_properties")
    site_properties = portal_properties.site_properties
    types_tool = getToolByName(context, "portal_types")
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

    if site_properties.hasProperty('enable_livesearch'):
        settings.enable_livesearch = site_properties.enable_livesearch
    settings.types_not_searched = tuple([
        t for t in types_tool.listContentTypes()
        if t in site_properties.types_not_searched and
        t not in BAD_TYPES
    ])


def upgrade_site_controlpanel_settings(context):
    """Copy site control panel settings from portal properties into the
       new registry.
    """
    # get the old site properties
    portal_properties = getToolByName(context, "portal_properties")
    site_properties = portal_properties.site_properties
    portal = getSite()
    # get the new registry
    registry = getUtility(IRegistry)
    # XXX: Somehow this code is executed for old migration steps as well
    # ( < Plone 4 ) and breaks because there is no registry. Looking up the
    # registry interfaces with 'check=False' will not work, because it will
    # return a settings object and then fail when we try to access the
    # attributes.
    try:
        settings = registry.forInterface(
            ISiteSchema,
            prefix='plone',
        )
    except KeyError:
        settings = False
    settings.site_title = unicode(portal.title)
    settings.webstats_js = unicode(site_properties.webstats_js)
    settings.enable_sitemap = site_properties.enable_sitemap
    if site_properties.hasProperty('exposeDCMetaTags'):
        settings.exposeDCMetaTags = site_properties.exposeDCMetaTags
