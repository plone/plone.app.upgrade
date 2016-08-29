# -*- coding: utf-8 -*-
from plone.app.upgrade.utils import loadMigrationProfile

import logging


logger = logging.getLogger('plone.app.upgrade')


def to51beta1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v51:to51beta1')
