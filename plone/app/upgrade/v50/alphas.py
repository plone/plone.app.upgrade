# -*- coding: utf-8 -*-
from Acquisition import aq_parent, aq_base
from plone.keyring.interfaces import IKeyManager
from plone.keyring.keyring import Keyring
from plone.keyring.keymanager import KeyManager
from zope.component import getUtility
from zope.component import getSiteManager
from zope.component.hooks import getSite
from Products.CMFCore.utils import getToolByName
from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.v40.alphas import cleanUpToolRegistry
import logging

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
    registry['plone.exposeDCMetaTags'] = site_props.exposeDCMetaTags
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
    if first_weekday is not None:
        # Set it. Otherwise, let plone.app.event install routine set it.
        registry['plone.first_weekday'] = first_weekday


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
