# -*- coding: utf-8 -*-
from plone.app.upgrade.utils import loadMigrationProfile
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IMarkupSchema
from Products.CMFPlone.utils import safe_unicode
from zope.component import getUtility

import logging


logger = logging.getLogger('plone.app.upgrade')


def rebuild_redirections(context):
    """Rebuild the plone.app.redirector information.

    This initializes the date and manual information.
    """
    from plone.app.redirector.interfaces import IRedirectionStorage

    storage = getUtility(IRedirectionStorage)
    if not hasattr(storage, '_rebuild'):
        logger.warning(
            'Not rebuilding redirections: '
            'IRedirectionStorage misses the _rebuild method. '
        )
        return
    logger.info(
        'Starting rebuild of redirections to '
        'add date and manual information.'
    )
    storage._rebuild()
    logger.info('Done rebuilding redirections.')


def move_dotted_to_named_behaviors(context):
    """named behaviors are better then dotted behaviors > let's move them."""
    from plone import api
    from plone.behavior.registration import lookup_behavior_registration
    from plone.dexterity.interfaces import IDexterityFTI

    ptt = api.portal.get_tool('portal_types')

    ftis = [fti for fti in ptt.objectValues() if IDexterityFTI.providedBy(fti)]

    for fti in ftis:
        behaviors = []
        for behavior in fti.behaviors:
            behavior_registration = lookup_behavior_registration(behavior)
            named_behavior = behavior_registration.name
            if named_behavior:
                behaviors.append(named_behavior)
                if named_behavior == behavior:
                    logger.info(
                        'Behavior "{behavior}" already named.'.format(
                            behavior=behavior,
                        ),
                    )
                else:
                    logger.info(
                        'Moved "{dotted}" to "{named}"'.format(
                            dotted=behavior,
                            named=named_behavior,
                        ),
                    )
            else:
                behaviors.append(behavior)
                logger.info(
                    '"{dotted}" has no name registered. '
                    'kept it dotted.'.format(
                        dotted=behavior,
                    ),
                )
        fti.behaviors = tuple(behaviors)
        logger.info(
            'Converted dotted behaviors of {ct} to named behaviors.'.format(
                ct=fti.title,
            ),
        )

    logger.info('Done moving dotted to named behaviors.')
    # Make sure plone.staticresources is installed
    from Products.CMFPlone.utils import get_installer
    qi = get_installer(context)
    if not qi.is_product_installed('plone.staticresources'):
        qi.install_product('plone.staticresources')


KEYS_TO_CHANGE = [
    "plone.always_show_selector",
    "plone.authenticated_users_only",
    "plone.available_languages",
    "plone.default_language",
    "plone.display_flags",
    "plone.set_cookie_always",
    "plone.use_cctld_negotiation",
    "plone.use_combined_language_codes",
    "plone.use_content_negotiation",
    "plone.use_cookie_negotiation",
    "plone.use_path_negotiation",
    "plone.use_request_negotiation",
    "plone.use_subdomain_negotiation",
]
_marker = dict()
OLD_PREFIX = "Products.CMFPlone.interfaces.ILanguageSchema"
NEW_PREFIX = "plone.i18n.interfaces.ILanguageSchema"


def change_interface_on_lang_registry_records(context):
    """Interface Products.CMFPlone.interfaces.ILanguageSchema was moved to
    plone.i18n.interfaces."""
    registry = getUtility(IRegistry)
    for postfix in KEYS_TO_CHANGE:
        old_key = OLD_PREFIX + "." + postfix
        record = registry.records.get(old_key, _marker)
        if record is _marker:
            continue
        logger.info(
            "Change registry key '{0}' to new interface.".format(old_key)
        )
        record.field.interfaceName = NEW_PREFIX


def to521(context):
    """5.2.0 -> 5.2.1"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v52:to521')
    # Make sure plone.staticresources is installed
    from Products.CMFPlone.utils import get_installer
    qi = get_installer(context)
    if not qi.is_product_installed('plone.staticresources'):
        qi.install_product('plone.staticresources')


def to522(context):
    """5.2.1 -> 5.2.2"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v52:to522')


def move_markdown_transform_settings_to_registry(context):
    """Move markdown settings from portal_transforms to Plone registry.
    """
    registry = getUtility(IRegistry)
    try:
        settings = registry.forInterface(IMarkupSchema, prefix='plone')
    except KeyError:
        # Catch case where markdown_extensions is not yet registered
        registry.registerInterface(IMarkupSchema, prefix='plone')
        settings = registry.forInterface(IMarkupSchema, prefix='plone')
    pt = getToolByName(context, 'portal_transforms')
    extensions = pt.markdown_to_html._config.get('enabled_extensions') or []
    extensions = [safe_unicode(ext) for ext in extensions]
    settings.markdown_extensions = extensions
