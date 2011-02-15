from plone.app.upgrade.utils import loadMigrationProfile


def to41beta1(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:to41beta1')
