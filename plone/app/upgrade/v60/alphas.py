# -*- coding: utf-8 -*-
from BTrees.OOBTree import OOBTree
from plone.app.upgrade.utils import cleanUpSkinsTool
from plone.app.upgrade.utils import loadMigrationProfile
from plone.dexterity.interfaces import IDexterityFTI
from plone.folder.nogopip import manage_addGopipIndex
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.tools.memberdata import MemberData
from zope.component import getUtility

import logging


logger = logging.getLogger('plone.app.upgrade')


def to60alpha1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v60:to60alpha1')
    # portal = getToolByName(context, 'portal_url').getPortalObject()

