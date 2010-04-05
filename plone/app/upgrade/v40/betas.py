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


def beta1_beta2(context):
    """4.0beta1 -> 4.0beta2
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:4beta1-4beta2')

def updateSafeHTMLConfig(context):
    """Update the safe_html transform with the new config params, migrating existing config from Kupu."""
    transform = getToolByName(context, 'portal_transforms').safe_html
    transform._tr_init(1) # load new config items
    kupu_tool = getToolByName(context, 'kupu_library_tool', None)
    if kupu_tool is None:
        return
    list_conf = dict(
        style_whitelist=kupu_tool.style_whitelist,
        class_blacklist=kupu_tool.class_blacklist,
        stripped_attributes=kupu_tool.get_stripped_attributes(),
        )
    for k, v in list_conf.items():
        tdata = transform._config[k]
        if tdata == v:
            continue
        while tdata:
            tdata.pop()
        tdata.extend(v)
    ksc = dict((str(' '.join(k)), str(' '.join(v))) for k, v in kupu_tool.get_stripped_combinations())
    tsc = transform._config['stripped_combinations']
    if tsc != ksc:
        tsc.clear()
        tsc.update(ksc)
    transform._p_changed = True
    transform.reload()
