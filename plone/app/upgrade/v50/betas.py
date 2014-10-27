# -*- coding: utf-8 -*-
from plone.app.upgrade.utils import loadMigrationProfile
import logging

logger = logging.getLogger('plone.app.upgrade')


def to50beta1(context):
    """5.0alpha3 - > 5.0beta1"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v50:to50alpha1')
