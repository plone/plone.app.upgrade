from Products.CMFCore.utils import getToolByName
from plone.app.upgrade.utils import loadMigrationProfile

def three2_three3(portal):
    """3.2.1 -> 3.3a1
    """
    loadMigrationProfile(portal, 'profile-plone.app.upgrade.v33:3.2.1-3.3a1')
    maybeUpdateLinkView(portal)

def three3_rc3_three3_rc4(portal):
    loadMigrationProfile(portal,'profile-plone.app.upgrade.v33:3.3rc3-3.3')
    cookCSSRegistries(portal)

def maybeUpdateLinkView(portal):
    ttool = getToolByName(portal, 'portal_types')
    link_fti = ttool.Link
    if link_fti.default_view == 'link_view':
        link_fti.view_methods = ('link_redirect_view',)
        link_fti.default_view = 'link_redirect_view'
        link_fti.immediate_view = 'link_redirect_view'

def cookCSSRegistries(portal):
    csstool = getToolByName(portal, 'portal_css')
    for resource in csstool.resources:
        resource.getCookedExpression()
    csstool.cookResources()
