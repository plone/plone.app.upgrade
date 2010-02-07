from plone.app.upgrade.utils import loadMigrationProfile

def alpha4_beta1(context):
    """4.0alpha4 -> 4.0beta1
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:4alpha4-4beta1')
