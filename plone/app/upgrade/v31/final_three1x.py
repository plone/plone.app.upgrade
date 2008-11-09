from plone.app.upgrade.utils import loadMigrationProfile

def three11_three12(portal):
    """3.1.1 -> 3.1.2"""
    
    out = []
    
    loadMigrationProfile(portal, 'profile-plone.app.upgrade:3.1.1-3.1.2')
