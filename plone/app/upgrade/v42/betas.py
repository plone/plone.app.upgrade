import logging
from plone.app.upgrade.utils import loadMigrationProfile

logger = logging.getLogger('plone.app.upgrade')


def to42beta1(context):
    """4.2a2 -> 4.2b1
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v42:to42beta1')

