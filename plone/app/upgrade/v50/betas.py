# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IMarkupSchema
from plone.registry.interfaces import IRegistry
from zope.component import getUtility


def upgrade_markup_controlpanel_settings(context):
    """Copy markup control panel settings from portal properties into the
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
            IMarkupSchema,
            prefix='plone',
        )
    except KeyError:
        settings = False
    if settings:
        settings.default_type = site_properties.default_contenttype

        forbidden_types = site_properties.getProperty('forbidden_contenttypes')
        forbidden_types = list(forbidden_types) if forbidden_types else []

        portal_transforms = getToolByName(context, 'portal_transforms')
        allowable_types = portal_transforms.listAvailableTextInputs()

        settings.allowed_types = tuple([
            _type for _type in allowable_types
            if _type not in forbidden_types
            and _type not in 'text/x-plone-outputfilters-html'  # removed, as in plone.app.vocabularies.types  # noqa
        ])
