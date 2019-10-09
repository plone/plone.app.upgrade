# -*- coding: utf-8 -*-
from plone.app.upgrade.utils import cleanUpSkinsTool
from plone.app.upgrade.utils import loadMigrationProfile
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from zExceptions import BadRequest
from zope.component import getUtility

import logging


logger = logging.getLogger('plone.app.upgrade')


def fix_i18n_domain(context):
    """Update i18n domain for some portal actions

    They used to have the plone.app.event domain,
    but now it is in plone domain.
    """
    atool = getToolByName(context, 'portal_actions')
    actions = atool.listActions()
    if not actions:
        return []

    actions_to_update = (
        'ical_import_settings',
        'ical_import_enable',
        'ical_import_disable',
    )
    for action_id in actions_to_update:
        try:
            action = atool['object'][action_id]
            action._updateProperty('i18n_domain', 'plone')
        except KeyError:
            logger.info(
                'Action object/%s was not found',
                action_id,
            )
        except BadRequest:
            logger.warn(
                'Action object/%s does not have an i18n_domain property',
                action_id,
            )


def remove_highlightsearchterms(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    cleanUpSkinsTool(portal)

    registry = getUtility(IRegistry)
    record = 'plone.bundles/plone-legacy.resources'
    resources = registry.records[record]
    if u'jquery-highlightsearchterms' in resources.value:
        resources.value.remove(u'jquery-highlightsearchterms')


def remove_old_PAE_rescources(context):  # noqa
    """FORCE remove old p.a.event resources"""
    registry = getUtility(IRegistry)
    resources = registry.records['plone.bundles/plone-legacy.resources']
    if u'resource-plone-app-event-event-js' in resources.value:
        resources.value.remove('resource-plone-app-event-event-js')
    if u'resource-plone-app-event-event-css' in resources.value:
        resources.value.remove('resource-plone-app-event-event-css')


def to517(context):
    """5.1.6 -> 5.1.7"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v51:to517')
