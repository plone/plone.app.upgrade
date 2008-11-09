from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.utils import loadMigrationProfile


def three1_beta1(portal):
    """3.1.7 -> 3.2beta1
    """
    actions = getToolByName(portal, 'portal_actions')
    if 'iterate_checkin' in actions.object_buttons.objectIds():
        loadMigrationProfile(
            portal,
            'profile-plone.app.upgrade.v32:3.2a1-3.2a2-iterate')
