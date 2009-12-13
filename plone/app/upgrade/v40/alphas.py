import transaction

from zope.app.cache.interfaces.ram import IRAMCache as OldIRAMCache
from zope.component import getSiteManager
from zope.ramcache.interfaces.ram import IRAMCache
from zope.ramcache.ram import RAMCache

from Acquisition import aq_base
from App.Common import package_home
from Products.MailHost.MailHost import MailHost
from Products.MailHost.interfaces import IMailHost
from Products.CMFCore.DirectoryView import _dirreg
from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.utils import logger
from plone.app.upgrade.utils import loadMigrationProfile


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
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:3-4alpha1')
    loadMigrationProfile(
        context, 'profile-Products.CMFPlone:dependencies',
        steps=('controlpanel', 'jsregistry'))


def restoreTheme(context):
    skins = getToolByName(context, 'portal_skins')
    portal = getToolByName(context, 'portal_url').getPortalObject()
    old_default_skin = getattr(aq_base(skins), 'old_default_skin', None)
    if old_default_skin is not None:
        setattr(aq_base(skins), 'default_skin', old_default_skin)
        portal.changeSkin(old_default_skin, context.REQUEST)

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
        cat = ic.getCategory()
        ident = ic.getActionId()
        expr = ic.getExpression()
        if expr.endswith('gif'):
            try:
                png_expr = expr[:-4] + '.png'
                portal.restrictedTraverse(png_expr)
                expr = png_expr
            except (AttributeError, KeyError):
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


def unregisterOldSteps(context):
    # remove steps that are now registered via ZCML or gone completely
    _REMOVE_STEPS = (
        'actions',
        'caching_policy_mgr',
        'catalog',
        'componentregistry',
        'content_type_registry',
        # 'languagetool',
        'mailhost',
        'properties',
        'rolemap',
        'skins',
        'toolset',
        'typeinfo',
        'workflow',
    )
    _REMOVE_IMPORT_STEPS = _REMOVE_STEPS + (
        'cookie_authentication',
        # 'mimetypes-registry-various',
        # 'plonepas',
        'plone-archetypes',
        'plone-site',
        'plone_various',
        # 'portal-transforms-various',
        'various',
    )
    _REMOVE_EXPORT_STEPS = _REMOVE_STEPS + (
        'cookieauth',
        'step_registries',
    )
    registry = context.getImportStepRegistry()
    steps = registry.listSteps()
    for step in _REMOVE_IMPORT_STEPS:
        if step in steps:
            registry.unregisterStep(step)
    registry = context.getExportStepRegistry()
    steps = registry.listSteps()
    for step in _REMOVE_EXPORT_STEPS:
        if step in steps:
            registry.unregisterStep(step)
    context._p_changed = True


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
            info = _dirreg.getDirectoryInfo(reg_key)
        except ValueError:
            skins._delObject(name)

    transaction.savepoint(optimistic=True)
    existing = skins.keys()
    # Remove no longer existing entries from skin selections
    for layer, paths in skins.selections.items():
        new_paths = []
        for name in paths.split(','):
            if name in existing:
                new_paths.append(name)
            elif name == 'plone_styles':
                # plone_styles has been moved and renamed
                new_paths.append('classic_styles')
        skins.selections[layer] = ','.join(new_paths)


def cleanUpProductRegistry(context):
    control = getattr(context, 'Control_Panel')
    products = control.Products

    gone = []
    for name, product in products.items():
        path = getattr(product, 'package_name', 'Products.' + product.id)
        try:
            prod_path = package_home({'__name__': path})
        except KeyError:
            gone.append(name)
        else:
            # Remove and reinitialize the help sections. Their internal
            # catalog has changed in Zope 2.12
            if product.get('Help'):
                product._delObject('Help')
                product.getProductHelp()

    # Remove product entries for products gone from the filesystem
    for name in gone:
        products._delObject(name)


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

    portal = getToolByName(context, 'portal_url').getPortalObject()
    MigrationView(portal, None)()


def recompilePythonScripts(context):
    """Recompile all Python Scripts"""
    portal = getToolByName(context, 'portal_url').getPortalObject()
    scripts = portal.ZopeFind(portal, obj_metatypes=('Script (Python)',),
                              search_sub=1)
    names = []
    for name, ob in scripts:
        if ob._v_change:
            names.append(name)
            ob._compile()
            ob._p_changed = 1

    if names:
        logger.info('The following Scripts were recompiled:\n' +
                    '\n'.join(names))


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
