# -*- coding: utf-8 -*-
from plone.app.upgrade.utils import loadMigrationProfile
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import logging


logger = logging.getLogger('plone.app.upgrade')

def to52alpha1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v52:to52alpha1')
