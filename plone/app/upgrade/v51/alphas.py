# -*- coding: utf-8 -*-
from plone.app.upgrade.utils import loadMigrationProfile
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import logging


logger = logging.getLogger('plone.app.upgrade')


def _fix_typo_in_toolbar_less_variable(context):
    registry = getUtility(IRegistry)
    _marker = list()

    plv = 'plone.lessvariables'
    value = registry[plv].get('plone-toolbar-font-secundary', _marker)
    if value == _marker:
        return
    if 'plone-toolbar-font-secondary' in registry[plv]:
        logger.warn(
            'Try to migrate registry value "plone-toolbar-font-secundary" to '
            '"plone-toolbar-font-secondary", but latter already exists. '
            'Migration to fix the typo is not executed.'
        )
        return
    registry[plv]['plone-toolbar-font-secondary'] = value
    del registry[plv]['plone-toolbar-font-secundary']


def to51alpha1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v51:to51alpha1')
    _fix_typo_in_toolbar_less_variable(context)


def to51alpha2(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v51:to51alpha2')
