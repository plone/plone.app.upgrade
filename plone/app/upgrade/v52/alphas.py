# -*- coding: utf-8 -*-
from plone.app.upgrade.utils import cleanUpSkinsTool
from plone.app.upgrade.utils import loadMigrationProfile
from plone.dexterity.interfaces import IDexterityFTI
from plone.folder.nogopip import manage_addGopipIndex
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility

import logging


logger = logging.getLogger('plone.app.upgrade')


def cleanup_resources():
    registry = getUtility(IRegistry)
    record = 'plone.bundles/plone-legacy.resources'
    resources = registry.records[record]

    if u'jquery-highlightsearchterms' in resources.value:
        resources.value.remove(u'jquery-highlightsearchterms')


def migrate_gopipindex(context):
    # GopipIndex class has moved from p.a.folder to p.folder
    # just remove and reinstall the index
    catalog = getToolByName(context, 'portal_catalog')
    catalog.manage_delIndex('getObjPositionInParent')
    manage_addGopipIndex(catalog, 'getObjPositionInParent')


def fix_core_behaviors_in_ftis(context):
    # The behaviors for IRichText and ILeadImage have been renamed.
    # All FTIs that use them must be updated accordingly
    # See plone/plone.app.contenttypes#480
    types_tool = getToolByName(context, 'portal_types')
    to_replace = {
        'plone.app.contenttypes.behaviors.richtext.IRichText':
            'plone.app.contenttypes.behaviors.richtext.IRichTextBehavior',
        'plone.app.contenttypes.behaviors.leadimage.ILeadImage':
            'plone.app.contenttypes.behaviors.leadimage.ILeadImageBehavior',
    }
    ftis = types_tool.listTypeInfo()
    for fti in ftis:
        # Since we're handling dexterity behaviors, we only care about
        # dexterity FTIs
        if not IDexterityFTI.providedBy(fti):
            continue
        behaviors = []
        change_needed = False
        for behavior in fti.behaviors:
            if behavior in to_replace:
                behavior = to_replace[behavior]
                change_needed = True
            behaviors.append(behavior)
        if change_needed:
            fti.behaviors = tuple(behaviors)


def to52alpha1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v52:to52alpha1')
    portal = getToolByName(context, 'portal_url').getPortalObject()
    cleanUpSkinsTool(portal)

    cleanup_resources()
    migrate_gopipindex(context)
    fix_core_behaviors_in_ftis(context)
