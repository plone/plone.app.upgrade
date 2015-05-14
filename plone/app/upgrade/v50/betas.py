# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IMailSchema
from Products.CMFPlone.interfaces import IMarkupSchema
from Products.CMFPlone.interfaces import ISecuritySchema
from Products.CMFPlone.interfaces import ILanguageSchema
from plone.app.upgrade.utils import loadMigrationProfile
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.component.hooks import getSite
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFPlone.interfaces.controlpanel import IImagingSchema


def to50beta1(context):
    """5.0alpha3 -> 5.0beta1"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v50:to50beta1')


def upgrade_portal_language(context):
    portal = getSite()
    registry = getUtility(IRegistry)
    # XXX: Somehow this code is executed for old migration steps as well
    # ( < Plone 4 ) and breaks because there is no registry. Looking up the
    # registry interfaces with 'check=False' will not work, because it will
    # return a settings object and then fail when we try to access the
    # attributes.
    try:
        lang_settings = registry.forInterface(ILanguageSchema, prefix='plone')
    except KeyError:
        return
    # Get old values

    # Merge default language options to registry
    portal = getUtility(ISiteRoot)
    if portal.hasProperty('default_language'):
        default_lang = portal.getProperty('default_language')

    portal_properties = getToolByName(context, "portal_properties", None)
    if portal_properties is not None:
        site_properties = getattr(portal_properties, 'site_properties', None)
        if site_properties is not None:
            if site_properties.hasProperty('default_language'):
                default_lang = site_properties.getProperty('default_language')
    lang_settings.default_language = default_lang
    if hasattr(portal, 'portal_languages'):
        portal_languages = getSite().portal_languages
        lang_settings.available_languages = portal_languages.supported_langs

        lang_settings.use_combined_language_codes = portal_languages.use_combined_language_codes  # noqa
        lang_settings.display_flags = portal_languages.display_flags

        lang_settings.use_path_negotiation = portal_languages.use_path_negotiation
        lang_settings.use_content_negotiation = portal_languages.use_content_negotiation
        lang_settings.use_cookie_negotiation = portal_languages.use_cookie_negotiation
        if hasattr(portal_languages, 'set_cookie_everywhere'):
            lang_settings.set_cookie_always = portal_languages.set_cookie_everywhere
        lang_settings.authenticated_users_only = portal_languages.authenticated_users_only
        lang_settings.use_request_negotiation = portal_languages.use_request_negotiation
        lang_settings.use_cctld_negotiation = portal_languages.use_cctld_negotiation
        lang_settings.use_subdomain_negotiation = portal_languages.use_subdomain_negotiation  # noqa
        if hasattr(portal_languages, 'always_show_selector'):
            lang_settings.always_show_selector = portal_languages.always_show_selector

        # Remove the old tool
        portal.manage_delObjects('portal_languages')

    # TODO: Remove portal skin
    # <object name="LanguageTool" meta_type="Filesystem Directory View"
    # directory="Products.PloneLanguageTool:skins/LanguageTool"/>


def upgrade_mail_controlpanel_settings(context):
    registry = getUtility(IRegistry)
    # XXX: Somehow this code is executed for old migration steps as well
    # ( < Plone 4 ) and breaks because there is no registry. Looking up the
    # registry interfaces with 'check=False' will not work, because it will
    # return a settings object and then fail when we try to access the
    # attributes.
    try:
        mail_settings = registry.forInterface(IMailSchema, prefix='plone')
    except KeyError:
        return
    portal = getSite()

    smtp_host = getattr(portal.MailHost, 'smtp_host', '')
    mail_settings.smtp_host = unicode(smtp_host)

    smtp_port = getattr(portal.MailHost, 'smtp_port', 25)
    mail_settings.smtp_port = smtp_port

    smtp_user_id = portal.MailHost.get('smtp_user_id')
    mail_settings.smtp_user_id = smtp_user_id

    smtp_pass = portal.MailHost.get('smtp_pass')
    mail_settings.smtp_pass = smtp_pass

    email_from_address = portal.get('email_from_address')
    mail_settings.email_from_address = email_from_address

    email_from_name = portal.get('email_from_name')
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
    # XXX: Somehow this code is executed for old migration steps as well
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

    # XXX: Somehow this code is executed for old migration steps as well
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


def to50beta2(context):
    """5.0beta1 -> 5.0beta2"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v50:to50beta2')
    portal = getSite()

    registry = getUtility(IRegistry)
    settings = registry.forInterface(IImagingSchema, prefix="plone")

    try:
        iprops = portal.portal_properties.imaging_properties

        settings.allowed_sizes = [s.decode('utf8') for s in iprops.getProperty('allowed_sizes')]  # noqa
        settings.quality = iprops.getProperty('quality')
    except AttributeError:
        # will only be there if from older plone instance
        pass