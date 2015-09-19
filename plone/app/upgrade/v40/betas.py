import transaction
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.CatalogTool import BLACKLISTED_INTERFACES
from zope.dottedname.resolve import resolve

from plone.app.upgrade.utils import logger
from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.utils import updateIconsInBrains


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
    transform._tr_init(1)  # load new config items
    kupu_tool = getToolByName(context, 'kupu_library_tool', None)
    if kupu_tool is None:
        return
    list_conf = []
    # Kupu sets its attributes on first use, rather than providing class level defaults.
    if hasattr(kupu_tool.aq_base, 'style_whitelist'):
        styles = list(kupu_tool.style_whitelist)
        if 'padding-left' not in styles:
            styles.append('padding-left')
        list_conf.append(('style_whitelist', styles))
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
    typesToUpdate = {
        'Document': ('document_icon.gif', 'document_icon.png'),
        'Event': ('event_icon.gif', 'event_icon.png'),
        'File': ('file_icon.gif', 'file_icon.png'),
        'Folder': ('folder_icon.gif', 'folder_icon.png'),
        'Image': ('image_icon.gif', 'image_icon.png'),
        'Link': ('link_icon.gif', 'link_icon.png'),
        'News Item': ('newsitem_icon.gif', 'newsitem_icon.png'),
        'Topic': ('topic_icon.gif', 'topic_icon.png'),
    }
    updateIconsInBrains(context, typesToUpdate)


def beta2_beta3(context):
    """4.0beta2 -> 4.0beta3
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:4beta2-4beta3')


def beta3_beta4(context):
    """4.0beta3 -> 4.0beta4
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:4beta3-4beta4')

    pprop = getToolByName(context, 'portal_properties')
    site_properties = pprop.site_properties
    if site_properties.hasProperty('typesLinkToFolderContentsInFC'):
        value = site_properties.getProperty('typesLinkToFolderContentsInFC')
        if 'Large Plone Folder' in value:
            value.remove('Large Plone Folder')
            site_properties.typesLinkToFolderContentsInFC = value

    navtree_properties = pprop.navtree_properties
    if navtree_properties.hasProperty('parentMetaTypesNotToQuery'):
        value = navtree_properties.getProperty('parentMetaTypesNotToQuery')
        if 'Large Plone Folder' in value:
            value.remove('Large Plone Folder')
            navtree_properties.parentMetaTypesNotToQuery = value


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
    """Convert files and images to blobs.

    We disable link integrity checks here, as the migration only
    removes objects to recreate them fresh, so in the end nothing is
    permanently removed.
    """
    logger.info('Started migration of files to blobs.')
    from plone.app.blob.migrations import migrateATBlobFiles
    sprop = getToolByName(context, 'portal_properties').site_properties
    if sprop.hasProperty('enable_link_integrity_checks'):
        ori_enable_link_integrity_checks = sprop.getProperty('enable_link_integrity_checks')
        if ori_enable_link_integrity_checks:
            logger.info('Temporarily disabled link integrity checking')
            sprop.enable_link_integrity_checks = False
    else:
        ori_enable_link_integrity_checks = None

    output = migrateATBlobFiles(context)
    count = len(output.split('\n')) - 1
    logger.info('Migrated %s files to blobs.' % count)

    logger.info('Started migration of images to blobs.')
    from plone.app.blob.migrations import migrateATBlobImages
    output = migrateATBlobImages(context)
    count = len(output.split('\n')) - 1
    logger.info('Migrated %s images to blobs.' % count)
    if ori_enable_link_integrity_checks:
        logger.info('Restored original link integrity checking setting')
        sprop.enable_link_integrity_checks = ori_enable_link_integrity_checks


def beta4_beta5(context):
    """4.0beta4 -> 4.0beta5
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:4beta4-4beta5')


def beta5_rc1(context):
    """4.0beta5 -> 4.0rc1
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:4beta5-4rc1')


def rc1_final(context):
    """4.0rc1 -> 4.0
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:4rc1-4final')


def four01(context):
    """4.0 -> 4.0.1
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:4.0-4.0.1')


def four02(context):
    """4.0.1 -> 4.0.2
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:4.0.1-4.0.2')


def four03(context):
    """4.0.2 -> 4.0.3
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:4.0.2-4.0.3')


def four04(context):
    """4.0.3 -> 4.0.4
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:4.0.3-4.0.4')


def fix_cataloged_interface_names(context):
    # some interfaces changed their canonical location, like
    # ATContentTypes.interface.* to interfaces.*
    # we also do the blacklist cleanup here, even though that was only
    # introduced in Plone 4.1 - but it saves us from walking the index twice
    catalog = getToolByName(context, 'portal_catalog')
    index = catalog._catalog.indexes.get('object_provides', None)
    if index is not None:
        logger.info('Updating `object_provides` index.')
        _index = index._index
        names = list(_index.keys())
        delete = set()
        rename = set()
        for name in names:
            try:
                klass = resolve(name)
            except ImportError:
                delete.add(name)
                del _index[name]
                index._length.change(-1)
                continue
            new_name = klass.__identifier__
            if new_name in BLACKLISTED_INTERFACES:
                delete.add(name)
                del _index[name]
                index._length.change(-1)
            elif name != new_name:
                rename.add(new_name)
                _index[new_name] = _index[name]
                delete.add(name)
                del _index[name]
                index._length.change(-1)
        if delete or rename:
            logger.info('Cleaning up `object_provides` _unindex.')
            _unindex = index._unindex
            for pos, (docid, value) in enumerate(_unindex.iteritems()):
                new_value = list(sorted((set(value) - delete).union(rename)))
                if value != new_value:
                    _unindex[docid] = new_value
                if pos and pos % 10000 == 0:
                    logger.info('Processed %s items.' % pos)
                    transaction.savepoint(optimistic=True)

    transaction.savepoint(optimistic=True)
    logger.info('Updated `object_provides` index.')


def four05(context):
    """4.0.4 -> 4.0.5
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:4.0.4-4.0.5')
    fix_cataloged_interface_names(context)
