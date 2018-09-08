# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from zExceptions import BadRequest

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
