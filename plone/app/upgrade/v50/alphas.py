import logging

from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.utils import loadMigrationProfile

logger = logging.getLogger('plone.app.upgrade')


def to50alpha1(context):
    """4.3 -> 5.0alpha1"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v50:to50alpha1')

    # remove obsolete tools
    portal = getToolByName(context, 'portal_url').getPortalObject()
    tools = ['portal_actionicons', 'portal_discussion', 'portal_undo']
    tools = [t for t in tools if t in portal]
    portal.manage_delObjects(tools)

    # remove layers from Products.CMFPlone
    layers_to_remove = ('plone_deprecated', )
    skins_tool = getToolByName(context, 'portal_skins')
    for layer in layers_to_remove:
        del skins_tool[layer]


def lowercase_email_login(context):
    """If email is used as login name, lowercase the login names.
    """
    ptool = getToolByName(context, 'portal_properties')
    if ptool.site_properties.getProperty('use_email_as_login'):
        # We want the login name to be lowercase here.  This is new in PAS.
        logger.info("Email is used as login, setting PAS login_transform to "
                    "'lower'.")
        # This can take a while for large sites, as it automatically
        # transforms existing login names to lowercase.  It will fail
        # if this would result in non-unique login names.
        pas = getToolByName(context, 'acl_users')
        pas.manage_changeProperties(login_transform='lower')
