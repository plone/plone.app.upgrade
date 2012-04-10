import logging
from plone.app.upgrade.utils import loadMigrationProfile

logger = logging.getLogger('plone.app.upgrade')


def to43alpha1(context):
    """4.2 -> 4.3alpha1
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v43:to43alpha1')
