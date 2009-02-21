from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.utils import loadMigrationProfile


def threeX_alpha1(context):
    """3.x -> 4.0alpha1
    """
    portal = getToolByName(context, 'portal_url').getPortalObject()
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:3-4alpha1')
