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


def remove_temp_folder(context):
    """Remove temp_folder from Zope root.

    See https://github.com/plone/Products.CMFPlone/issues/2957
    """
    try:
        from Products.ZODBMountPoint.MountedObject import MountedObject
    except ImportError:
        MountedObject = None
    app = context.unrestrictedTraverse('/')
    if "temp_folder" not in app:
        logger.info("No temp_folder found in Zope root, so no cleanup needed.")
        return
    logger.info("Checking if temp_folder needs to be removed from Zope root. "
                "Note: this may log several ZConfig.ConfigurationErrors.")
    # We cannot catch ZConfig.ConfigurationError with try/except.
    temp_folder = app.temp_folder
    if MountedObject is not None:
        if not isinstance(temp_folder, MountedObject):
            logger.info("Not removing temp_folder from Zope root: it is not from class MountedObject.")
            return
    if not hasattr(temp_folder, "mount_error_"):
        logger.info("Not removing temp_folder from Zope root: it has no attribute mount_error_.")
        return
    if not temp_folder.mount_error_():
        logger.info("Not removing temp_folder from Zope root: there is no mount error. "
                    "In plone.recipe.zope2instance set zodb-temporary-storage=off if you want to get rid of it.")
        return
    # TODO: does this work when the user is Manager at the Plone site level but not at the Zope root.?
    # I think it does, but we should check.
    app._delObject("temp_folder")
    logger.info("temp_folder removed from Zope root.")


def to60alpha1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v60:to60alpha1')
    # portal = getToolByName(context, 'portal_url').getPortalObject()
