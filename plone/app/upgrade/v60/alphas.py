# -*- coding: utf-8 -*-
from plone.app.upgrade.utils import loadMigrationProfile

import logging


logger = logging.getLogger('plone.app.upgrade')


def to60alpha1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v60:to60alpha1')


def remove_temp_folder(context):
    """Remove temp_folder from Zope root if broken."""
    from ZODB.broken import Broken

    app = context.unrestrictedTraverse("/")
    broken_id = "temp_folder"
    if broken_id in app.objectIds():
        temp_folder = app.unrestrictedTraverse(broken_id, None)
        if not isinstance(temp_folder, Broken):
            logger.info("%s is not broken, so we keep it.", broken_id)
            return
        app._delObject(broken_id)
        logger.info("Removed broken %s from Zope root.", broken_id)

    # The root Zope object has a dictionary '_mount_points.
    # >>> app._mount_points
    # {'temp_folder': MountedObject(id='temp_folder')}
    if not hasattr(app, "_mount_points"):
        return
    if broken_id in app._mount_points:
        del app._mount_points[broken_id]
        app._p_changed = True
        logger.info("Removed %s from Zope root _mount_points.", broken_id)
