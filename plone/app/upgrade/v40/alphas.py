from zope.app.cache.interfaces.ram import IRAMCache as OldIRAMCache
from zope.component import getSiteManager
from zope.ramcache.interfaces.ram import IRAMCache
from zope.ramcache.ram import RAMCache

from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.utils import logger
from plone.app.upgrade.utils import loadMigrationProfile


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

def threeX_alpha1(context):
    """3.x -> 4.0alpha1
    """
    portal = getToolByName(context, 'portal_url').getPortalObject()
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v40:3-4alpha1')


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
