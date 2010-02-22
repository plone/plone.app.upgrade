from plone.app.upgrade.utils import logger
from plone.app.upgrade.utils import loadMigrationProfile

def alpha5_beta1(context):
    """4.0alpha5 -> 4.0beta1
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:4alpha5-4beta1')