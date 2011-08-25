import logging
from plone.app.upgrade.utils import loadMigrationProfile

logger = logging.getLogger('plone.app.upgrade')


def to42alpha1(context):
    """4.1 -> 4.2alpha1
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v42:to42alpha1')


def to42alpha2(context):
    """4.2a1 -> 4.2a2
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v42:to42alpha2')
