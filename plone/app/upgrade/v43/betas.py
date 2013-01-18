from plone.app.upgrade.utils import loadMigrationProfile

def to43beta2(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v43:to43beta2')


def upgradeSunburst(context):
    """ Upgrade plonetheme.sunburst to version 1.4
    """
    from plonetheme.sunburst.setuphandlers import upgrade_step_2_3
    upgrade_step_2_3(context)