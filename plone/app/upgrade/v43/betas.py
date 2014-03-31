from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.v43.alphas import upgradeToI18NCaseNormalizer

def to43beta2(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v43:to43beta2')

def to43rc1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v43:to43rc1')
    upgradeToI18NCaseNormalizer(context)


def upgradeSunburst(context):
    """ Upgrade plonetheme.sunburst to version 1.4
    """
    try:
        from plonetheme.sunburst.setuphandlers import upgrade_step_2_3
    except ImportError:
        pass
    else:
        upgrade_step_2_3(context)
