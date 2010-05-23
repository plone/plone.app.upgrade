from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.utils import logger
from plone.app.upgrade.utils import loadMigrationProfile


def alpha5_beta1(context):
    """4.0alpha5 -> 4.0beta1"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:4alpha5-4beta1')


def repositionRecursiveGroupsPlugin(context):
    """If the recursive groups plugin is active, make sure it's at the bottom of the active plugins list"""
    from Products.PluggableAuthService.interfaces.plugins import IGroupsPlugin
    acl = getToolByName(context, 'acl_users')
    plugins = acl.plugins
    existingGroupsPlugins = plugins.listPlugins(IGroupsPlugin)
    if 'recursive_groups' in [a[0] for a in existingGroupsPlugins]:
        while plugins.getAllPlugins('IGroupsPlugin')['active'].index('recursive_groups') < len(existingGroupsPlugins)-1:
            plugins.movePluginsDown(IGroupsPlugin, ['recursive_groups'])


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
    list_conf = []
    # Kupu sets its attributes on first use, rather than providing class level defaults.
    if hasattr(kupu_tool.aq_base, 'style_whitelist'):
        list_conf.append(('style_whitelist', kupu_tool.style_whitelist))
    if hasattr(kupu_tool.aq_base, 'class_blacklist'):
        list_conf.append(('class_blacklist', kupu_tool.class_blacklist))
    if hasattr(kupu_tool.aq_base, 'html_exclusions'):
        list_conf.append(('stripped_attributes', kupu_tool.get_stripped_attributes()))
    for k, v in list_conf:
        tdata = transform._config[k]
        if tdata == v:
            continue
        while tdata:
            tdata.pop()
        tdata.extend(v)
    if hasattr(kupu_tool.aq_base, 'html_exclusions'):
        ksc = dict((str(' '.join(k)), str(' '.join(v))) for k, v in kupu_tool.get_stripped_combinations())
        tsc = transform._config['stripped_combinations']
        if tsc != ksc:
            tsc.clear()
            tsc.update(ksc)
    transform._p_changed = True
    transform.reload()


def updateIconMetadata(context):
    """Update getIcon metadata column for all core content"""
    catalog = getToolByName(context, 'portal_catalog')
    search = catalog.unrestrictedSearchResults
    reindex = catalog.reindexObject
    typesToUpdate = [
        'Document', 'Event', 'File', 'Folder', 'Image',
        'Link', 'News_Item', 'Plone_Site', 'TempFolder',
        'Topic',
        ]
    for typeName in typesToUpdate:
        for brain in search(portal_type=typeName):
            obj = brain.getObject()
            # Abuse this step to conveniently get rid of old persistent
            # uppercase Interface records
            if '__implements__' in obj.__dict__:
                del obj.__dict__['__implements__']
                obj._p_changed = True
            # passing in a valid but inexpensive index, makes sure we don't
            # reindex the entire catalog including expensive indexes like
            # SearchableText
            reindex(obj, idxs=['id'])
        logger.info('Updated `getIcon` for %s content' % typeName)


def beta2_beta3(context):
    """4.0beta2 -> 4.0beta3
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:4beta2-4beta3')


def beta3_beta4(context):
    """4.0beta3 -> 4.0beta4
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:4beta3-4beta4')


def removeLargePloneFolder(context):
    """Complete removal of Large Plone Folder
    (Most of it is accomplished by the profile.)
    """
    ftool = getToolByName(context, 'portal_factory')
    l = set(ftool.getFactoryTypes())
    if 'Large Plone Folder' in l:
        l.remove('Large Plone Folder')
        ftool.manage_setPortalFactoryTypes(listOfTypeIds=list(l))


def convertToBlobs(context):
    logger.info('Started migration of files to blobs.')
    from plone.app.blob.migrations import migrateATBlobFiles
    output = migrateATBlobFiles(context)
    count = len(output.split('\n')) - 1
    logger.info('Migrated %s files to blobs.' % count)

    logger.info('Started migration of images to blobs.')
    from plone.app.blob.migrations import migrateATBlobImages
    output = migrateATBlobImages(context)
    count = len(output.split('\n')) - 1
    logger.info('Migrated %s images to blobs.' % count)
