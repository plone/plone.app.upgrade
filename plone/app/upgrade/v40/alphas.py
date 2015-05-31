import transaction

from zope.component import queryMultiAdapter
from zope.component import getUtilitiesFor
from zope.component import getSiteManager, getUtility
from zope.ramcache.interfaces.ram import IRAMCache
from zope.ramcache.ram import RAMCache

from Acquisition import aq_base
from Acquisition import aq_get
from Products.CMFCore.CachingPolicyManager import manage_addCachingPolicyManager
from Products.CMFCore.DirectoryView import _dirreg
from Products.CMFCore.interfaces import ICachingPolicyManager
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.setuphandlers import addCacheHandlers
from Products.CMFPlone.setuphandlers import addCacheForResourceRegistry
from Products.MailHost.MailHost import MailHost
from Products.MailHost.interfaces import IMailHost
from zExceptions import NotFound
from plone.app.viewletmanager.interfaces import IViewletSettingsStorage

from plone.app.upgrade.utils import logger
from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.utils import unregisterSteps
from plone.portlet.static.static import IStaticPortlet
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import IPortletAssignmentSettings
from plone.portlets.interfaces import IPortletManager

from Products.CMFCore.Expression import Expression


_KNOWN_ACTION_ICONS = {
    'plone': ['sendto', 'print', 'rss', 'extedit', 'full_screen',
              'addtofavorites', 'ics', 'vcs'],
    'object_buttons': ['cut', 'copy', 'paste', 'delete',
                       'iterate_checkin', 'iterate_checkout',
                       'iterate_checkout_cancel'],
    'folder_buttons': ['cut', 'copy', 'paste', 'delete'],
    'controlpanel': ['QuickInstaller', 'portal_atct', 'MailHost',
                     'UsersGroups', 'MemberPrefs', 'PortalSkin',
                     'MemberPassword', 'ZMI', 'SecuritySettings',
                     'NavigationSettings', 'SearchSettings',
                     'errorLog', 'kupu', 'PloneReconfig',
                     'CalendarSettings', 'TypesSettings',
                     'PloneLanguageTool', 'CalendarSettings',
                     'HtmlFilter', 'Maintenance', 'UsersGroups2',
                     'versioning', 'placefulworkflow',
                     'MarkupSettings', 'ContentRules'],
}


def updateToolset(context):
    # This must happen before other upgrade steps using GS profiles can be
    # successfully run.
    name = 'profile-plone.app.upgrade.v40:update-toolset'
    loadMigrationProfile(context, name)


def rememberTheme(context):
    skins = getToolByName(context, 'portal_skins')
    default_skin = getattr(skins, 'default_skin', '')
    setattr(aq_base(skins), 'old_default_skin', default_skin)


def threeX_alpha1(context):
    """3.x -> 4.0alpha1
    """
    try:
        import plone.app.jquerytools
        loadMigrationProfile(context, 'profile-plone.app.jquerytools:default')
    except ImportError:
        pass
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:3-4alpha1')
    loadMigrationProfile(
        context, 'profile-Products.CMFPlone:dependencies',
        steps=('controlpanel', 'jsregistry'))
    # Install plonetheme.classic profile
    # (if, installed, it will be removed in Plone 5)
    qi = getToolByName(context, 'portal_quickinstaller')
    stool = getToolByName(context, 'portal_setup')
    if 'plonetheme.classic' in qi:
        stool.runAllImportStepsFromProfile(
            'profile-plonetheme.classic:default'
        )
    # Install packages that are needed for Plone 4,
    # but don't break on Plone 5 where they are gone
    for profile in ('archetypes.referencebrowserwidget:default',
            'plonetheme.sunburst:default',
            'Products.TinyMCE:TinyMCE'):
        try:
            stool.runAllImportStepsFromProfile('profile-' + profile)
        except KeyError:
            pass

def restoreTheme(context):
    skins = getToolByName(context, 'portal_skins')
    portal = getToolByName(context, 'portal_url').getPortalObject()
    old_default_skin = getattr(aq_base(skins), 'old_default_skin', None)

    if old_default_skin == 'Plone Default':
        v_storage = getUtility(IViewletSettingsStorage)
        uncustomized_layers = ('custom,tinymce,referencebrowser,LanguageTool,cmfeditions_views,'
                              'CMFEditions,kupu_plone,kupu,kupu_tests,archetypes,archetypes_kss,'
                              'mimetypes_icons,plone_kss,ATContentTypes,PasswordReset,'
                              'plone_ecmascript,plone_wysiwyg,plone_prefs,plone_templates,'
                              'classic_styles,plone_form_scripts,plone_scripts,plone_forms,'
                              'plone_images,plone_content,plone_login,plone_deprecated,'
                              'plone_3rdParty,cmf_legacy')
        if skins.selections.get('Plone Default') == uncustomized_layers:
            # if the old theme's layers hadn't been mucked with, we can just
            # use Plone Classic Theme
            old_default_skin = 'Plone Classic Theme'
        else:
            # otherwise, copy Plone Default to a new theme
            skins.selections['Old Plone 3 Custom Theme'] = skins.selections.get('Plone Default')
            # copy the viewlet order
            v_storage._order['Old Plone 3 Custom Theme'] = dict(v_storage._order.get('Plone Default', {}))
            v_storage._hidden['Old Plone 3 Custom Theme'] = dict(v_storage._hidden.get('Plone Default', {}))

            old_default_skin = 'Old Plone 3 Custom Theme'

        # reset the Plone Default theme to the standard layers and viewlets
        skins.selections['Plone Default'] = ''
        v_storage._order['Plone Default'] = {}
        v_storage._hidden['Plone Default'] = {}
        loadMigrationProfile(context, 'profile-Products.CMFPlone:plone',
                             steps=('skins', 'viewlets'))

    if old_default_skin is not None:
        setattr(aq_base(skins), 'default_skin', old_default_skin)
        request = aq_get(context, 'REQUEST', None)
        portal.changeSkin(old_default_skin, request)

    # The Sunburst theme is based on Plone Default. During the cleanUpSkinsTool
    # upgrade step we replace plone_styles with classic_styles in the default
    # theme. As a result Sunburst includes ``classic_styles`` at this point.
    theme = 'Sunburst Theme'
    paths = skins.selections.get(theme)
    if paths:
        new_paths = []
        for path in paths.split(','):
            if path != 'classic_styles':
                new_paths.append(path)
        skins.selections[theme] = ','.join(new_paths)


def setupReferencebrowser(context):
    # remove obsolete skin 'ATReferenceBrowserWidget' from skins tool
    portal = getToolByName(context, 'portal_url').getPortalObject()
    skins_tool = getToolByName(portal, 'portal_skins')
    sels = skins_tool._getSelections()
    for skinname, layer in sels.items():
        layers = layer.split(',')
        if 'ATReferenceBrowserWidget' in layers:
            layers.remove('ATReferenceBrowserWidget')
        new_layers = ','.join(layers)
        sels[skinname] = new_layers


def migrateActionIcons(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    atool = getToolByName(portal, 'portal_actions', None)
    cptool = getToolByName(portal, 'portal_controlpanel', None)
    aitool = getToolByName(portal, 'portal_actionicons', None)

    if atool is None or cptool is None or aitool is None:
        return

    # Existing action categories
    categories = atool.objectIds()

    for ic in aitool.listActionIcons():
        cat = ic._category
        ident = ic._action_id
        expr = ic._icon_expr_text
        try:
            expr = str(expr)
        except UnicodeEncodeError:
            pass
        if expr.endswith('gif'):
            try:
                png_expr = expr[:-4] + '.png'
                portal.restrictedTraverse(png_expr)
                expr = png_expr
            except (AttributeError, KeyError, TypeError, NotFound):
                pass
        prefix = ''

        if (cat not in _KNOWN_ACTION_ICONS.keys() or
            ident not in _KNOWN_ACTION_ICONS[cat]):
            continue

        prefix = ''
        if ':' not in expr:
            prefix = 'string:$portal_url/'

        if cat == 'plone':
            new_cat = 'document_actions'
        else:
            new_cat = cat
        if new_cat in categories:
            # actions tool
            action = atool[new_cat].get(ident)
            if action is not None:
                if not action.icon_expr:
                    action._setPropValue('icon_expr', '%s%s' % (prefix, expr))
        elif cat == 'controlpanel':
            # control panel tool
            action_infos = [a for a in cptool.listActions()
                              if a.getId() == ident]
            if len(action_infos):
                if not action_infos[0].getIconExpression():
                    action_infos[0].setIconExpression('%s%s' % (prefix, expr))

        # Remove the action icon
        aitool.removeActionIcon(cat, ident)


def addOrReplaceRamCache(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    sm = getSiteManager(context=portal)
    from zope.app.cache.interfaces.ram import IRAMCache as OldIRAMCache
    sm.unregisterUtility(provided=OldIRAMCache)
    sm.unregisterUtility(provided=IRAMCache)
    sm.registerUtility(factory=RAMCache, provided=IRAMCache)
    logger.info('Installed local RAM cache utility.')


def changeWorkflowActorVariableExpression(context):
    wftool = getToolByName(context, 'portal_workflow')
    workflows = ('intranet_folder_workflow', 'one_state_workflow',
                 'simple_publication_workflow')
    for workflow_id in workflows:
        wf = getattr(wftool, workflow_id, None)
        if wf is None:
            continue
        actor_var = wf.variables._getOb('actor', None)
        if actor_var is None:
            continue
        actor_var.setProperties(description = actor_var.description,
                                default_expr = 'user/getId',
                                for_status = 1,
                                update_always = 1)
    logger.info('Updated workflow actor variable expression.')


def changeAuthenticatedResourcesCondition(context):
    """ ResourceRegistries now has an 'authenticated' boolean property which
        can be used to short-circuit the expression evaluation for the simple,
        common case of authenticated-only resources.
    """
    resources = {
        'portal_css': ('member.css', ),
        'portal_javascripts': ('dropdown.js', 'table_sorter.js',
            'calendar_formfield.js', 'calendarpopup.js', 'formUnload.js',
            'formsubmithelpers.js', 'unlockOnFormUnload.js')}
    ANON = ('not: portal/portal_membership/isAnonymousUser',
            'not:portal/portal_membership/isAnonymousUser', )
    for tool_id, resource_ids in resources.items():
        tool = getToolByName(context, tool_id, None)
        if tool is None:
            continue
        for resource_id in resource_ids:
            resource = tool.getResource(resource_id)
            if resource is None:
                continue
            if resource._data['expression'] in ANON:
                resource.setExpression('')
                resource.setAuthenticated(True)
        tool.cookResources()
    logger.info('Updated expression for authenticated-only resources.')


def cleanPloneSiteFTI(context):
    portal_types = getToolByName(context, 'portal_types', None)

    site = portal_types['Plone Site']
    to_remove = ['edit', 'folderlisting', 'external_edit']
    actids = [o.id for o in site.listActions()]
    selection = [actids.index(a) for a in actids if a in to_remove]
    if len(selection) > 0:
        site.deleteActions(selection)
        logger.info('Updated Plone site FTI.')

    temp = portal_types['TempFolder']
    to_remove = ['edit', 'localroles', 'folderContents']
    actids = [o.id for o in temp.listActions()]
    selection = [actids.index(a) for a in actids if a in to_remove]
    if len(selection) > 0:
        temp.deleteActions(selection)
        logger.info('Updated TempFolder FTI.')


def removeBrokenCacheFu(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    cpm = getattr(portal, 'caching_policy_manager', None)
    if cpm and cpm.getId() == 'broken':
        # If we detect a broken CacheFu install, remove it
        CACHEFU_IDS = [
            'CacheSetup_OFSCache',
            'CacheSetup_PageCache',
            'caching_policy_manager',
            'HTTPCache',
            'portal_cache_settings',
            'portal_squid',
        ]
        cpm = aq_base(cpm)
        for i in CACHEFU_IDS:
            portal._delOb(i)
        objects = portal._objects
        portal._objects = tuple(
            [i for i in objects if getattr(portal, i['id'], None)])
        sm = getSiteManager(context=portal)
        sm.unregisterUtility(component=cpm, provided=ICachingPolicyManager)
        del cpm
        transaction.savepoint(optimistic=True)
        manage_addCachingPolicyManager(portal)
        addCacheHandlers(portal)
        addCacheForResourceRegistry(portal)
        logger.info('Removed CacheSetup tools.')


def unregisterOldSteps(context):
    # remove steps that are now registered via ZCML or gone completely
    _REMOVE_IMPORT_STEPS = [
        'caching_policy_mgr',
        'cookie_authentication',
        'plone-archetypes',
        'plone-site',
        'plone_various',
        'various',
    ]
    _REMOVE_EXPORT_STEPS = [
        'caching_policy_mgr',
        'cookieauth',
        'step_registries',
    ]
    unregisterSteps(context, import_steps=_REMOVE_IMPORT_STEPS,
                    export_steps=_REMOVE_EXPORT_STEPS)


def cleanUpToolRegistry(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    toolset = context.getToolsetRegistry()
    required = toolset._required.copy()
    existing = portal.keys()
    changed = False
    for name, info in required.items():
        if name not in existing:
            del required[name]
            changed = True
    if changed:
        toolset._required = required
        logger.info('Cleaned up the toolset registry.')


def cleanUpSkinsTool(context):
    skins = getToolByName(context, 'portal_skins')
    # Remove directory views for directories missing on the filesystem
    for name in skins.keys():
        directory_view = skins.get(name)
        reg_key = getattr(directory_view, '_dirpath', None)
        if not reg_key:
            # not a directory view, but a persistent folder
            continue
        try:
            reg_key = _dirreg.getCurrentKeyFormat(reg_key)
            _dirreg.getDirectoryInfo(reg_key)
        except ValueError:
            skins._delObject(name)

    transaction.savepoint(optimistic=True)
    existing = skins.keys()
    # Remove no longer existing entries from skin selections
    for layer, paths in skins.selections.items():
        new_paths = []
        for name in paths.split(','):
            if name == 'plone_styles':
                # plone_styles has been moved and renamed
                new_paths.append('classic_styles')
            elif name in existing:
                new_paths.append(name)
        skins.selections[layer] = ','.join(new_paths)


def cleanUpProductRegistry(context):
    control = getattr(context, 'Control_Panel')
    products = control.Products

    # Remove all product entries
    for name in products.keys():
        products._delObject(name)


def migrateStaticTextPortlets(context):
    """ Missing import step from #9286 Allow to show/hide portlets """
    def migrate_portlets_for_object(obj, path):
        portlet_managers = getUtilitiesFor(IPortletManager, context=obj)
        for portlet_manager_name, portlet_manager in portlet_managers:
            assignments = queryMultiAdapter(
                (obj, portlet_manager), IPortletAssignmentMapping, context=obj)
            if assignments is None:
                continue
            for portlet_id, portlet in assignments.items():
                if IStaticPortlet.providedBy(portlet) and \
                        getattr(portlet, 'hide', False):
                    logger.info(
                            'Found hidden static text portlet %s at %s' %
                            (portlet_id, path))
                    settings = IPortletAssignmentSettings(portlet)
                    settings['visible'] = False

    logger.info('Migrating static text portlets')
    portal = getToolByName(context, 'portal_url').getPortalObject()
    portal.ZopeFindAndApply(
            portal, search_sub=True, apply_func=migrate_portlets_for_object)
    logger.info('Finished migrating static text portlets')


def migrateMailHost(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    mh = getToolByName(portal, 'MailHost', None)
    if mh is None:
        return

    # Migrate secure mail host and broken mail host objects
    meta_type = getattr(mh, 'meta_type', None)
    if meta_type in ('Secure Mail Host', 'Broken Because Product is Gone'):
        if meta_type == 'Secure Mail Host':
            new_mh = MailHost(
                id=mh.id,
                title=mh.title,
                smtp_host=mh.smtp_host,
                smtp_port=mh.smtp_port,
                smtp_uid=mh.smtp_userid or '',
                smtp_pwd=mh.smtp_pass or '',
                force_tls=False,
            )
        else:
            new_mh = MailHost(id='MailHost', smtp_host='')
            logger.info('Replaced a broken MailHost object.')
        portal._delObject('MailHost')
        portal._setObject('MailHost', new_mh)
        sm = getSiteManager(context=portal)
        sm.unregisterUtility(provided=IMailHost)
        sm.registerUtility(new_mh, provided=IMailHost)


def migrateFolders(context):
    from plone.app.folder.migration import BTreeMigrationView

    class MigrationView(BTreeMigrationView):

        def mklog(self):
            msgs = []

            def log(msg, timestamp=True, cr=True):
                msgs.append(msg)
                if cr:
                    logger.info(''.join(msgs))
                    msgs[:] = []
            return log

        def postprocess(self, obj):
            # Recompile any Python script with stale code
            meta_type = getattr(aq_base(obj), 'meta_type', None)
            if meta_type == 'Script (Python)':
                if obj._v_change:
                    obj._compile()
                    obj._p_changed = 1
            # Abuse this step to conveniently get rid of old persistent
            # uppercase Interface records
            if '__implements__' in obj.__dict__:
                del obj.__dict__['__implements__']
                obj._p_changed = 1

    portal = getToolByName(context, 'portal_url').getPortalObject()
    transaction.savepoint(optimistic=True)
    MigrationView(portal, None)()


def renameJoinFormFields(context):
    """Rename portal_properties join_form_fields to registration_fields"""
    sprop = getToolByName(context, 'portal_properties').site_properties
    if sprop.hasProperty('join_form_fields'):
        oldValue = list(sprop.getProperty('join_form_fields'))
        # The 'groups' field no longer belongs in the user-facing registration form
        if 'groups' in oldValue:
            oldValue.remove('groups')
        if not sprop.hasProperty('user_registration_fields'):
            sprop.manage_addProperty('user_registration_fields', oldValue, 'lines')
        sprop.manage_delProperties(['join_form_fields'])


def alpha2_alpha3(context):
    """4.0alpha2 -> 4.0alpha3
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:4alpha2-4alpha3')


def updateLargeFolderType(context):
    """Update portal type of former 'Large Folder' content"""
    catalog = getToolByName(context, 'portal_catalog')
    search = catalog.unrestrictedSearchResults
    reindex = catalog.reindexObject

    def update(brain):
        obj = brain.getObject()
        obj._setPortalTypeName('Folder')
        reindex(obj, idxs=['portal_type', 'Type', 'object_provides'])

    # [:] copies the search results; without this we miss some of them
    # due to the reindexing in update()
    for brain in search(portal_type='Large Plone Folder')[:]:
        update(brain)
    for brain in search(Type='Large Folder'):   # just to make sure...
        update(brain)
    logger.info('Updated `portal_type` for former "Large Folder" content')


def addRecursiveGroupsPlugin(context):
    """Add a recursive groups plugin to acl_users"""
    from Products.PluggableAuthService.plugins.RecursiveGroupsPlugin import addRecursiveGroupsPlugin, IRecursiveGroupsPlugin
    from Products.PluggableAuthService.interfaces.plugins import IGroupsPlugin
    acl = getToolByName(context, 'acl_users')
    plugins = acl.plugins

    existingPlugins = plugins.listPlugins(IGroupsPlugin)
    if existingPlugins:
        for p, id in existingPlugins:
            if IRecursiveGroupsPlugin.providedBy(p):
                plugins.deactivatePlugin(IGroupsPlugin, id)
                logger.warn('Found an existing Recursive Groups plugin, %s, in acl_users, deactivating.' % id)

    if not 'recursive_groups' in acl:
        addRecursiveGroupsPlugin(acl, 'recursive_groups', "Recursive Groups Plugin")


def cleanUpClassicThemeResources(context):
    """
    Remove the metadata of all registered CSS resources for the
    plonetheme.classic product so they don't get unregistered when the
    product is uninstalled. These registrations now live in
    Products.CMFPlone.
    """
    qi = getToolByName(context, 'portal_quickinstaller')
    if 'plonetheme.classic' in qi:
        classictheme = qi['plonetheme.classic']
        classictheme.resources_css = []  # empty the list of installed resources


def migrateTypeIcons(context):
    """
    Remove content_icon value of all content types
    and set a default icon_expr value with old content_icon value string.
    """
    ttool = getToolByName(context, 'portal_types')
    for type in ttool.values():
        if 'content_icon' in type.__dict__:
            icon = type.content_icon
            if icon and not getattr(type, 'icon_expr', False):
                type.icon_expr = "string:${portal_url}/%s" % icon
                type.icon_expr_object = Expression(type.icon_expr)
                del type.content_icon


def alpha4_alpha5(context):
    """4.0alpha4 -> 4.0alpha5
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:4alpha4-4alpha5')
