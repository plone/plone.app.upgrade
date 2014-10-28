# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IEditingSchema
from plone.app.upgrade.utils import loadMigrationProfile
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

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
