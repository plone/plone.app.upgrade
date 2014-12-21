# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IMailSchema
from Products.CMFPlone.interfaces import IMarkupSchema
from Products.CMFPlone.interfaces import ISecuritySchema
from plone.app.upgrade.utils import loadMigrationProfile
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.component.hooks import getSite


def to50beta1(context):
    """5.0alpha3 -> 5.0beta1"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v50:to50beta1')


def upgrade_mail_controlpanel_settings(context):
    registry = getUtility(IRegistry)
    # XXX: Somehow this code is excecuted for old migration steps as well
    # ( < Plone 4 ) and breaks because there is no registry. Looking up the
    # registry interfaces with 'check=False' will not work, because it will
    # return a settings object and then fail when we try to access the
    # attributes.
    try:
        mail_settings = registry.forInterface(IMailSchema, prefix='plone')
    except KeyError:
        return
    portal = getSite()
    portal_properties = getToolByName(context, "portal_properties")

    smtp_host = getattr(portal.MailHost, 'smtp_host', '')
    mail_settings.smtp_host = unicode(smtp_host)

    smtp_port = getattr(portal.MailHost, 'smtp_port', 25)
    mail_settings.smtp_port = smtp_port

    smtp_user_id = portal.MailHost.get('smtp_user_id')
    mail_settings.smtp_user_id = smtp_user_id

    smtp_pass = portal.MailHost.get('smtp_pass')
    mail_settings.smtp_pass = smtp_pass

    email_from_address = portal_properties.get('email_from_address')
    mail_settings.email_from_address = email_from_address

    email_from_name = portal_properties.get('email_from_name')
    mail_settings.email_from_name = email_from_name


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


def upgrade_security_controlpanel_settings(context):
    """Copy security control panel settings from portal properties and various
    other locations into the new registry.
    """
    def _get_enable_self_reg():
        app_perms = portal.rolesOfPermission(permission='Add portal member')
        for appperm in app_perms:
            if appperm['name'] == 'Anonymous' and \
               appperm['selected'] == 'SELECTED':
                return True
        return False

    # get the old site properties
    portal_url = getToolByName(context, 'portal_url')
    portal = portal_url.getPortalObject()
    portal_properties = getToolByName(portal, "portal_properties")
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
            ISecuritySchema,
            prefix='plone',
        )
    except KeyError:
        settings = False
    if settings:
        settings.enable_self_reg = _get_enable_self_reg()
        validate_email = portal.getProperty('validate_email', True)
        if validate_email:
            settings.enable_user_pwd_choice = False
        else:
            settings.enable_user_pwd_choice = True
        pmembership = getToolByName(portal, 'portal_membership')
        settings.enable_user_folders = pmembership.getMemberareaCreationFlag()
        settings.allow_anon_views_about = site_properties.getProperty(
            'allowAnonymousViewAbout', False)
        settings.use_email_as_login = site_properties.getProperty(
            'use_email_as_login', False)
        settings.use_uuid_as_userid = site_properties.getProperty(
            'use_uuid_as_userid', False)
