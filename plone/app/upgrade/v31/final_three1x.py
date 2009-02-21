from plone.app.upgrade.utils import loadMigrationProfile

def three14_three15(portal):
    """3.1.4 -> 3.1.5"""

    out = []

    loadMigrationProfile(portal, 'profile-plone.app.upgrade.v31:3.1.3-3.1.4')
