from plone.app.upgrade.utils import loadMigrationProfile

def to43beta2(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v43:to43beta2')
