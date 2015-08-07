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
        # Is the package still there?  Not on Plone 5.
        import plonetheme.sunburst
        plonetheme.sunburst  # pyflakes
    except ImportError:
        return
    context.upgradeProfile('plonetheme.sunburst:default', dest='3')
