from plone.app.upgrade.utils import logger
from plone.app.upgrade.utils import loadMigrationProfile
from Products.CMFCore.utils import getToolByName

def alpha5_beta1(context):
    """4.0alpha5 -> 4.0beta1
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:4alpha5-4beta1')
    

def repositionRecursiveGroupsPlugin(context):
    """If the recursive groups plugin is active, make sure it's at the bottom of the active plugins list"""
    from Products.PluggableAuthService.interfaces.plugins import IGroupsPlugin
    acl = getToolByName(context, 'acl_users')
    plugins = acl.plugins
    existingGroupsPlugins = plugins.listPlugins(IGroupsPlugin)
    if 'recursive_groups' in [a[0] for a in existingGroupsPlugins]:
        while plugins.getAllPlugins('IGroupsPlugin')['active'].index('recursive_groups') < len(existingGroupsPlugins)-1:
            plugins.movePluginsDown(IGroupsPlugin,['recursive_groups'])
