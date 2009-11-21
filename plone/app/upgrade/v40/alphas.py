import transaction

from zope.app.cache.interfaces.ram import IRAMCache as OldIRAMCache
from zope.component import getSiteManager
from zope.ramcache.interfaces.ram import IRAMCache
from zope.ramcache.ram import RAMCache

from Products.MailHost.MailHost import MailHost
from Products.MailHost.interfaces import IMailHost
from Products.CMFCore.DirectoryView import _dirreg
from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.utils import logger
from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.utils import installOrReinstallProduct


_KNOWN_ACTION_ICONS = {
    'plone' : ['sendto', 'print', 'rss', 'extedit', 'full_screen',
               'addtofavorites', 'ics', 'vcs'],
    'object_buttons' : ['cut', 'copy', 'paste', 'delete',
                        'iterate_checkin', 'iterate_checkout',
                        'iterate_checkout_cancel'],
    'folder_buttons' : ['cut', 'copy', 'paste', 'delete'],
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
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:update-toolset')

def threeX_alpha1(context):
    """3.x -> 4.0alpha1
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:3-4alpha1')

def installJqTools(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    installOrReinstallProduct(portal, 'plone.app.jquerytools')

def setupReferencebrowser(context):
    # install new archetypes.referencebrowserwidget
    portal = getToolByName(context, 'portal_url').getPortalObject()
    qi = getToolByName(portal, 'portal_quickinstaller')
    package = 'archetypes.referencebrowserwidget'
    if not qi.isProductInstalled(package):
        qi.installProduct(package, locked=True)
        logger.info("Installed %s" % package)

    # remove obsolete skin 'ATReferenceBrowserWidget' from skins tool
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

        if cat not in _KNOWN_ACTION_ICONS.keys() or ident not in _KNOWN_ACTION_ICONS[cat]:
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
            action_infos = [a for a in cptool.listActions() if a.getId() == ident]
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
        'portal_css': ('member.css',),
        'portal_javascripts': ('dropdown.js', 'table_sorter.js',
            'calendar_formfield.js', 'calendarpopup.js', 'formUnload.js',
            'formsubmithelpers.js', 'unlockOnFormUnload.js')
        }
    for tool_id, resource_ids in resources.items():
        tool = getToolByName(context, tool_id, None)
        if tool is None:
            continue
        for resource_id in resource_ids:
            resource = tool.getResource(resource_id)
            if resource is None:
                continue
            if resource._data['expression'] == 'not: portal/portal_membership/isAnonymousUser':
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

def unregisterOldImportSteps(context):
    # remove steps that are now registered via ZCML or gone completely
    REMOVE = (
        'plone-archetypes',
        'plone-site',
        'plone_various',
    )
    registry = context.getImportStepRegistry()
    steps = registry.listSteps()
    for step in REMOVE:
        if step in steps:
            registry.unregisterStep(step)

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
        skins.selections[layer] = ','.join(new_paths)

def migrateMailHost(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    mh = getToolByName(portal, 'MailHost', None)
    # Only migrate secure mail host
    if mh and getattr(mh, 'meta_type', None) == 'Secure Mail Host':
        new_mh = MailHost(id=mh.id, title=mh.title, smtp_host=mh.smtp_host,
                          smtp_port=mh.smtp_port, smtp_uid=mh.smtp_userid or '',
                          smtp_pwd=mh.smtp_pass or '', force_tls=False)
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
