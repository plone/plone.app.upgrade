from zope.app.cache.interfaces.ram import IRAMCache as OldIRAMCache
from zope.component import getSiteManager
from zope.ramcache.interfaces.ram import IRAMCache
from zope.ramcache.ram import RAMCache

from Products.MailHost.MailHost import MailHost
from Products.MailHost.interfaces import IMailHost
from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.utils import logger
from plone.app.upgrade.utils import loadMigrationProfile


_KNOWN_ACTION_ICONS = {
    'plone' : ['sendto', 'print', 'rss', 'extedit', 'full_screen'],
    'object_buttons' : ['cut', 'copy', 'paste', 'delete'],
    'folder_buttons' : ['cut', 'copy', 'paste', 'delete'],
    'controlpanel': ['QuickInstaller', 'portal_atct', 'MailHost',
                       'UsersGroups', 'MemberPrefs', 'PortalSkin',
                       'MemberPassword', 'ZMI', 'SecuritySettings',
                       'NavigationSettings', 'SearchSettings',
                       'errorLog', 'kupu', 'PloneReconfig',
                       'CalendarSettings', 'TypesSettings', 
                       'PloneLanguageTool', 'CalendarSettings',
                       'HtmlFilter', 'Maintenance', 'UsersGroups2',
                       'versioning', 'placefulworkflow'],
}

def threeX_alpha1(context):
    """3.x -> 4.0alpha1
    """
    portal = getToolByName(context, 'portal_url').getPortalObject()
    migrateMailHost(portal)
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
        prefix = ''
        
        if cat not in _KNOWN_ACTION_ICONS.keys() or ident not in _KNOWN_ACTION_ICONS[cat]:
            continue
        
        prefix = ''
        if ':' not in expr:
            prefix = 'string:$portal_url/'

        if cat in categories:
            # actions tool
            action = atool[cat].get(ident)
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

def migrateMailHost(portal):
    mh = getToolByName(portal, 'MailHost', None)
    # Only migrate secure mail host
    if mh and getattr(mh, 'meta_type', None) == 'Secure Mail Host':
        new_mh = MailHost(id=mh.id, title=mh.title, smtp_host=mh.smtp_host,
                          smtp_port=mh.smtp_port, smtp_uid=mh.smtp_userid,
                          smtp_pwd=mh.smtp_pass, force_tls=False)
        portal._delObject('MailHost')
        portal._setObject('MailHost', new_mh)
        sm = getSiteManager(context=portal)
        sm.unregisterUtility(provided=IMailHost)
        sm.registerUtility(new_mh, provided=IMailHost)
