# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from plone.app.upgrade.utils import loadMigrationProfile
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.interfaces import IEditingSchema
from Products.CMFPlone.interfaces import INavigationSchema
from Products.CMFPlone.interfaces import IMaintenanceSchema
from Products.CMFPlone.interfaces import ISearchSchema
from Products.CMFPlone.interfaces import ISiteSchema
from plone.app.vocabularies.types import BAD_TYPES
from zope.component import getUtility
from zope.site.hooks import getSite

import logging

logger = logging.getLogger('plone.app.upgrade')


def to50beta1(context):
    """5.0alpha3 - > 5.0beta1"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v50:to50alpha1')


def upgrade_editing_controlpanel_settings(context):
    """Copy editing control panel settings from portal properties into the new
       registry.
    """
    # get the old site properties
    portal_properties = getToolByName(context, "portal_properties")
    site_properties = portal_properties.site_properties
    # get the new registry
    registry = getUtility(IRegistry)
    # XXX: Somehow this code is excecuted for old migration steps as well
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
        settings.visible_ids = site_properties.visible_ids
        settings.enable_link_integrity_checks = \
            site_properties.enable_link_integrity_checks
        settings.ext_editor = site_properties.ext_editor
        #settings.available_editors = site_properties.available_editors
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
    # XXX: Somehow this code is excecuted for old migration steps as well
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
    # XXX: Somehow this code is excecuted for old migration steps as well
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
    # XXX: Somehow this code is excecuted for old migration steps as well
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

    settings.enable_livesearch = site_properties.enable_livesearch
    settings.types_not_searched = tuple([
        t for t in types_tool.listContentTypes()
        if t not in site_properties.types_not_searched and
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
    # XXX: Somehow this code is excecuted for old migration steps as well
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
    settings.exposeDCMetaTags = site_properties.exposeDCMetaTags
