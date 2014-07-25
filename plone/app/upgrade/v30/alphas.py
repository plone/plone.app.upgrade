import os

from five.localsitemanager import find_next_sitemanager
from five.localsitemanager import make_objectmanager_site
from five.localsitemanager.registry import FiveVerifyingAdapterLookup
from five.localsitemanager.registry import PersistentComponents
from plone.app.portlets.utils import convert_legacy_portlets
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import ILocalPortletAssignmentManager
from plone.portlets.constants import CONTEXT_CATEGORY as CONTEXT_PORTLETS
from zope.location.interfaces import ISite
from zope.component import getMultiAdapter
from zope.component import getSiteManager
from zope.component import getUtility
from zope.component.globalregistry import base
from zope.component.interfaces import ComponentLookupError
from zope.site.hooks import setSite

from Acquisition import aq_base
from App.Common import package_home
from Products.Archetypes.interfaces import IArchetypeTool
from Products.Archetypes.interfaces import IReferenceCatalog
from Products.Archetypes.interfaces import IUIDCatalog
from Products.CMFActionIcons.interfaces import IActionIconsTool
from Products.CMFCalendar.interfaces import ICalendarTool
from Products.CMFCore.ActionInformation import Action
from Products.CMFCore.ActionInformation import ActionCategory
from Products.CMFCore.interfaces import IActionsTool
from Products.CMFCore.interfaces import ICachingPolicyManager
from Products.CMFCore.interfaces import ICatalogTool
from Products.CMFCore.interfaces import IContentTypeRegistry
from Products.CMFCore.interfaces import IDiscussionTool
from Products.CMFCore.interfaces import IMemberDataTool
from Products.CMFCore.interfaces import IMembershipTool
from Products.CMFCore.interfaces import IMetadataTool
from Products.CMFCore.interfaces import IPropertiesTool
from Products.CMFCore.interfaces import IRegistrationTool
from Products.CMFCore.interfaces import ISiteRoot
from Products.CMFCore.interfaces import ISkinsTool
from Products.CMFCore.interfaces import ISyndicationTool
from Products.CMFCore.interfaces import ITypesTool
from Products.CMFCore.interfaces import IUndoTool
from Products.CMFCore.interfaces import IURLTool
from Products.CMFCore.interfaces import IConfigurableWorkflowTool
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.DirectoryView import createDirectoryView
from Products.CMFDiffTool.interfaces import IDiffTool
from Products.CMFEditions.interfaces import IArchivistTool
from Products.CMFEditions.interfaces import IPortalModifierTool
from Products.CMFEditions.interfaces import IPurgePolicyTool
from Products.CMFEditions.interfaces.IRepository import IRepositoryTool
from Products.CMFEditions.interfaces import IStorageTool
from Products.CMFFormController.interfaces import IFormControllerTool
from Products.CMFQuickInstallerTool.interfaces import IQuickInstallerTool
from Products.CMFUid.interfaces import IUniqueIdAnnotationManagement
from Products.CMFUid.interfaces import IUniqueIdGenerator
from Products.CMFUid.interfaces import IUniqueIdHandler
from Products.DCWorkflow.DCWorkflow import DCWorkflowDefinition
from Products.DCWorkflow.exportimport import WorkflowDefinitionConfigurator, _initDCWorkflow
from Products.GenericSetup.interfaces import ISetupTool
from Products.MailHost.interfaces import IMailHost
from Products.MimetypesRegistry.interfaces import IMimetypesRegistryTool
from Products.PloneLanguageTool.interfaces import ILanguageTool
from Products.PlonePAS.interfaces.group import IGroupTool
from Products.PlonePAS.interfaces.group import IGroupDataTool
from Products.PortalTransforms.interfaces import IPortalTransformsTool
from Products.ResourceRegistries.interfaces import ICSSRegistry
from Products.ResourceRegistries.interfaces import IJSRegistry
from Products.StandardCacheManagers import RAMCacheManager

from Products.CMFPlone import cmfplone_globals
from Products.CMFPlone.factory import _DEFAULT_PROFILE
from Products.CMFPlone.interfaces import IPloneSiteRoot
from Products.CMFPlone.interfaces import IPloneTool
from Products.CMFPlone.interfaces import ITranslationServiceTool

from plone.app.upgrade.utils import installOrReinstallProduct
from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.utils import logger

try:
    from Products.ATContentTypes.interface import IATCTTool
    from Products.ATContentTypes.migration.v1_2 import upgradeATCTTool
    HAS_ATCT = True
except ImportError:
    HAS_ATCT = False

try:
    from Products.CMFPlone.interfaces import IFactoryTool
except:
    from Products.ATContentTypes.interfaces import IFactoryTool


def three0_alpha1(context):
    """2.5.x -> 3.0-alpha1
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v30:2.5.x-3.0a1')

    portal = getToolByName(context, 'portal_url').getPortalObject()

    # The ATCT tool has lost all type migration functionality and quite some
    # metadata and index information stored on it needs to be updated.
    if HAS_ATCT:
        upgradeATCTTool(portal)

    # Install CMFEditions and CMFDiffTool
    installProduct('CMFEditions', portal, hidden=True)


def alpha1_alpha2(context):
    """ 3.0-alpha1 -> 3.0-alpha2
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v30:3.0a1-3.0a2')


def alpha2_beta1(context):
    """ 3.0-alpha2 -> 3.0-beta1
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v30:3.0a2-3.0b1')

    portal = getToolByName(context, 'portal_url').getPortalObject()

    # Install PloneLanguageTool
    installProduct('PloneLanguageTool', portal, hidden=True)


def enableZope3Site(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    if not ISite.providedBy(portal):
        make_objectmanager_site(portal)
        logger.info('Made the portal a Zope3 site.')
    try:
        components = portal.getSiteManager()
    except ComponentLookupError:
        next = find_next_sitemanager(portal)
        if next is None:
            next = base
        name = '/'.join(portal.getPhysicalPath())
        components = PersistentComponents(name, (next,))
        components.__parent__ = portal
        portal.setSiteManager(components)
        logger.info("Site manager '%s' added." % name)
    else:
        if components.utilities.LookupClass != FiveVerifyingAdapterLookup:
            # for CMF 2.1 beta instances
            components.__parent__ = portal
            components.utilities.LookupClass = FiveVerifyingAdapterLookup
            components.utilities._createLookup()
            components.utilities.__parent__ = components
            logger.info('LookupClass replaced.')
    # Make sure to set the new site as the new active one
    setSite(portal)


def migrateOldActions(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    special_providers = ['portal_controlpanel',
                         'portal_types',
                         'portal_workflow']
    # We don't need to operate on the providers that are still valid and
    # should ignore the control panel as well
    providers = [obj for obj in portal.objectValues()
                     if hasattr(obj, '_actions') and
                     obj.getId() not in special_providers]
    non_empty_providers = [p for p in providers if len(p._actions) > 0]
    for provider in non_empty_providers:
        for action in provider._actions:
            category = action.category
            # check if the category already exists, otherwise create it
            new_category = getattr(aq_base(portal.portal_actions), category, None)
            if new_category is None:
                portal.portal_actions._setObject(category, ActionCategory(id=category))
                new_category = portal.portal_actions[category]

            # Special handling for Expressions
            url_expr = ''
            if action.action:
                url_expr = action.action.text
            available_expr = ''
            if action.condition:
                available_expr = action.condition.text

            new_action = Action(action.id,
                title=action.title,
                description=action.description,
                url_expr=url_expr,
                available_expr=available_expr,
                permissions=action.permissions,
                visible = action.visible)

            # Only add an action if there isn't one with that name already
            if getattr(aq_base(new_category), action.id, None) is None:
                new_category._setObject(action.id, new_action)

        # Remove old actions from upgraded providers
        provider._actions = ()
    logger.info('Upgraded old actions to new actions stored in portal_actions.')


def _check_ascii(text):
    try:
        unicode(text, 'ascii')
    except UnicodeDecodeError:
        return False
    return True


def updateActionsI18NDomain(context):
    actions = getToolByName(context, 'portal_actions')
    actions = actions.listActions()
    domainless_actions = [a for a in actions if not a.i18n_domain]
    for action in domainless_actions:
        if _check_ascii(action.title) and _check_ascii(action.description):
            action.i18n_domain = 'plone'
    if domainless_actions:
        logger.info('Updated actions i18n domain attribute.')


def updateFTII18NDomain(context):
    types = getToolByName(context, 'portal_types')
    types = types.listTypeInfo()
    domainless_types = [fti for fti in types if not fti.i18n_domain]
    for fti in domainless_types:
        if _check_ascii(fti.title) and _check_ascii(fti.description):
            fti.i18n_domain = 'plone'
    if domainless_types:
        logger.info('Updated type informations i18n domain attribute.')


def addPortletManagers(context):
    """Add new portlets managers."""
    loadMigrationProfile(context, 'profile-Products.CMFPlone:plone',
            steps=['portlets'])


def convertLegacyPortlets(context):
    """Convert portlets defined in left_slots and right_slots at the portal
    root to use plone.portlets. Also block portlets in the Members folder.

    Note - there may be other portlets defined elsewhere. These will require
    manual upgrade from the @@manage-portlets view. This is to avoid a
    full walk of the portal (i.e. waking up every single object) looking for
    potential left_slots/right_slots!
    """
    portal = getToolByName(context, 'portal_url').getPortalObject()
    convert_legacy_portlets(portal)
    logger.info('Converted legacy portlets at the portal root')
    logger.info('NOTE: You may need to convert other portlets manually.')
    logger.info(' - to do so, click "manage portlets" in the relevant folder.')

    members = getattr(portal, 'Members', None)
    if members is not None:
        membersRightSlots = getattr(aq_base(members), 'right_slots', None)
        if membersRightSlots == []:
            rightColumn = getUtility(IPortletManager, name=u'plone.rightcolumn', context=portal)
            portletAssignments = getMultiAdapter((members, rightColumn,), ILocalPortletAssignmentManager)
            portletAssignments.setBlacklistStatus(CONTEXT_PORTLETS, True)
            logger.info('Blacklisted contextual portlets in the Members folder')


def installProduct(product, portal, out=None, hidden=False):
    """Quickinstalls a product if it is not installed yet."""
    if out is None:
        out = []
    installOrReinstallProduct(portal, product, out, hidden=hidden)


registration = (('mimetypes_registry', IMimetypesRegistryTool),
                ('portal_transforms', IPortalTransformsTool),
                ('portal_actionicons', IActionIconsTool),
                ('portal_discussion', IDiscussionTool),
                ('portal_metadata', IMetadataTool),
                ('portal_properties', IPropertiesTool),
                ('portal_syndication', ISyndicationTool),
                ('portal_undo', IUndoTool),
                ('MailHost', IMailHost),
                ('portal_diff', IDiffTool),
                ('portal_uidannotation', IUniqueIdAnnotationManagement),
                ('portal_uidgenerator', IUniqueIdGenerator),
               )
if HAS_ATCT:
    registration += (('portal_atct', IATCTTool),)

invalid_regs = (ILanguageTool, IArchivistTool, IPortalModifierTool,
                IPurgePolicyTool, IRepositoryTool, IStorageTool,
                IFormControllerTool, IReferenceCatalog, IUIDCatalog,
                ICalendarTool, IActionsTool, ICatalogTool,
                IContentTypeRegistry, ISkinsTool, ITypesTool, IURLTool,
                IConfigurableWorkflowTool, IPloneTool, ICSSRegistry,
                IJSRegistry, IUniqueIdHandler, IFactoryTool, IMembershipTool,
                IGroupTool, IGroupDataTool, IMemberDataTool,
                ICachingPolicyManager, IRegistrationTool, IArchetypeTool,
                ITranslationServiceTool, IQuickInstallerTool,
                ISetupTool,
               )

def registerToolsAsUtilities(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    sm = getSiteManager(portal)

    portalregistration = ((portal, ISiteRoot),
                          (portal, IPloneSiteRoot),)

    for reg in portalregistration:
        if sm.queryUtility(reg[1]) is None:
            sm.registerUtility(aq_base(reg[0]), reg[1])

    for reg in registration:
        if sm.queryUtility(reg[1]) is None:
            if reg[0] in portal.keys():
                tool = aq_base(portal[reg[0]])
                sm.registerUtility(tool, reg[1])

    for reg in invalid_regs:
        if sm.queryUtility(reg) is not None:
            sm.unregisterUtility(provided=reg)

    logger.info("Registered tools as utilities.")


def addReaderAndEditorRoles(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    if 'Reader' not in portal.valid_roles():
        portal._addRole('Reader')
    if 'Editor' not in portal.valid_roles():
        portal._addRole('Editor')
    if 'Reader' not in portal.acl_users.portal_role_manager.listRoleIds():
        portal.acl_users.portal_role_manager.addRole('Reader')
    if 'Editor' not in portal.acl_users.portal_role_manager.listRoleIds():
        portal.acl_users.portal_role_manager.addRole('Editor')

    viewRoles = [r['name'] for r in portal.rolesOfPermission('View') if r['selected']]
    modifyRoles = [r['name'] for r in portal.rolesOfPermission('Modify portal content') if r['selected']]

    if 'Reader' not in viewRoles:
        viewRoles.append('Reader')
        portal.manage_permission('View', viewRoles, True)

    if 'Editor' not in modifyRoles:
        modifyRoles.append('Editor')
        portal.manage_permission('Modify portal content', modifyRoles, True)

    logger.info('Added reader and editor roles')


def migrateLocalroleForm(context):
    portal_types = getToolByName(context, 'portal_types', None)
    if portal_types is not None:
        for fti in portal_types.objectValues():
            if not hasattr(fti, '_aliases'):
                fti._aliases={}

            aliases = fti.getMethodAliases()
            new_aliases = aliases.copy()
            for k, v in aliases.items():
                if 'folder_localrole_form' in v:
                    new_aliases[k] = v.replace('folder_localrole_form', '@@sharing')
            fti.setMethodAliases(new_aliases)

            for a in fti.listActions():
                expr = a.getActionExpression()
                if 'folder_localrole_form' in expr:
                    a.setActionExpression(expr.replace('folder_localrole_form', '@@sharing'))
    logger.info('Ensured references to folder_localrole_form point to @@sharing now')


def reorderUserActions(context):
    portal_actions = getToolByName(context, 'portal_actions', None)
    if portal_actions is not None:
        user_category = getattr(portal_actions, 'user', None)
        if user_category is not None:
            new_actions = ['login', 'join', 'mystuff', 'preferences', 'undo', 'logout']
            new_actions.reverse()
            for action in new_actions:
                if action in user_category.objectIds():
                    user_category.moveObjectsToTop([action])


def updateMemberSecurity(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    pprop = getToolByName(portal, 'portal_properties')
    portal.manage_permission('Add portal member', roles=['Manager','Owner'], acquire=0)
    pprop.site_properties.manage_changeProperties(allowAnonymousViewAbout=False)

    portal.manage_changeProperties(validate_email=True)

    pmembership = getToolByName(portal, 'portal_membership')
    pmembership.memberareaCreationFlag = 0
    logger.info("Updated member management security")


def updatePASPlugins(context):
    from Products.PlonePAS.Extensions.Install import activatePluginInterfaces

    portal = getToolByName(context, 'portal_url').getPortalObject()

    activatePluginInterfaces(portal, 'mutable_properties')
    activatePluginInterfaces(portal, 'source_users')
    activatePluginInterfaces(portal, 'credentials_cookie_auth',
            disable=['ICredentialsResetPlugin', 'ICredentialsUpdatePlugin'])
    if not portal.acl_users.objectIds(['Plone Session Plugin']):
        from plone.session.plugins.session import manage_addSessionPlugin
        manage_addSessionPlugin(portal.acl_users, 'session')
        activatePluginInterfaces(portal, "session")
        logger.info("Added Plone Session Plugin.")


def updateConfigletTitles(portal):
    """Update titles of some configlets"""
    controlPanel = getToolByName(portal, 'portal_controlpanel', None)
    if controlPanel is not None:
        collection = controlPanel.getActionObject('Plone/portal_atct')
        language = controlPanel.getActionObject('Plone/PloneLanguageTool')
        navigation = controlPanel.getActionObject('Plone/NavigationSettings')
        types = controlPanel.getActionObject('Plone/TypesSettings')
        users = controlPanel.getActionObject('Plone/UsersGroups')
        users2 = controlPanel.getActionObject('Plone/UsersGroups2')

        if collection is not None:
            collection.title = "Collection"
        if language is not None:
            language.title = "Language"
        if navigation is not None:
            navigation.title = "Navigation"
        if types is not None:
            types.title = "Types"
        if users is not None:
            users.title = "Users and Groups"
        if users2 is not None:
            users2.title = "Users and Groups"


def updateKukitJS(context):
    """Use the unpacked kukit-src.js and pack it ourself.
    """
    jsreg = getToolByName(context, 'portal_javascripts', None)
    old_id = '++resource++kukit.js'
    new_id = '++resource++kukit-src.js'
    if jsreg is not None:
        script_ids = jsreg.getResourceIds()
        if old_id in script_ids and new_id in script_ids:
            jsreg.unregisterResource(old_id)
        elif old_id in script_ids:
            jsreg.renameResource(old_id, new_id)
            logger.info("Use %s instead of %s" % (new_id, old_id))
        resource = jsreg.getResource(new_id)
        if resource is not None:
            resource.setCompression('full')
            logger.info("Set 'full' compression on %s" % new_id)


def addCacheForResourceRegistry(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    ram_cache_id = 'ResourceRegistryCache'
    if not ram_cache_id in portal.objectIds():
        RAMCacheManager.manage_addRAMCacheManager(portal, ram_cache_id)
        cache = getattr(portal, ram_cache_id)
        settings = cache.getSettings()
        settings['max_age'] = 24*3600 # keep for up to 24 hours
        settings['request_vars'] = ('URL',)
        cache.manage_editProps('Cache for saved ResourceRegistry files', settings)
        logger.info('Created RAMCache %s for ResourceRegistry output' % ram_cache_id)
    reg = getToolByName(portal, 'portal_css', None)
    if reg is not None and getattr(aq_base(reg), 'ZCacheable_setManagerId', None) is not None:
        reg.ZCacheable_setManagerId(ram_cache_id)
        reg.ZCacheable_setEnabled(1)
        logger.info('Associated portal_css with %s' % ram_cache_id)
    reg = getToolByName(portal, 'portal_javascripts', None)
    if reg is not None and getattr(aq_base(reg), 'ZCacheable_setManagerId', None) is not None:
        reg.ZCacheable_setManagerId(ram_cache_id)
        reg.ZCacheable_setEnabled(1)
        logger.info('Associated portal_javascripts with %s' % ram_cache_id)


def removeTablelessSkin(context):
    st = getToolByName(context, 'portal_skins')
    if 'Plone Tableless' in st.getSkinSelections():
        st.manage_skinLayers(['Plone Tableless'], del_skin=True)
        logger.info("Removed the Plone Tableless skin")
    if st.default_skin=='Plone Tableless':
        st.default_skin='Plone Default'
        logger.info("Changed the default skin to 'Plone Default'")


def addObjectProvidesIndex(context):
    """Add the object_provides index to the portal_catalog.
    """
    catalog = getToolByName(context, 'portal_catalog')
    if 'object_provides' not in catalog.indexes():
        catalog.addIndex('object_provides', 'KeywordIndex')
        logger.info("Added object_provides index to portal_catalog")


def removeMyStuffAction(context):
    """The mystuff action is now covered by the dashboard"""
    actions = getToolByName(context, 'portal_actions')
    if getattr(actions, 'user', None) is None:
        return
    category=actions.user
    if 'mystuff' in category.objectIds():
        category.manage_delObjects(ids=['mystuff'])
        logger.info("Removed the mystuff user action")


def addMissingWorkflows(context):
    """Add new Plone 3.0 workflows
    """
    portal = getToolByName(context, 'portal_url').getPortalObject()
    wft = getToolByName(portal, 'portal_workflow', None)
    if wft is None:
        return

    new_workflow_ids = [ 'intranet_workflow', 'intranet_folder_workflow',
                        'one_state_workflow', 'simple_publication_workflow']
    encoding = 'utf-8'
    path_prefix = os.path.join(package_home(cmfplone_globals), 'profiles',
            'default', 'workflows')

    for wf_id in new_workflow_ids:
        if wf_id in wft.objectIds():
            logger.info("Workflow %s already installed; doing nothing" % wf_id)
            continue

        path = os.path.join(path_prefix, wf_id, 'definition.xml')
        body = open(path,'r').read()

        wft._setObject(wf_id, DCWorkflowDefinition(wf_id))
        wf = wft[wf_id]
        wfdc = WorkflowDefinitionConfigurator(wf)

        ( workflow_id
        , title
        , state_variable
        , initial_state
        , states
        , transitions
        , variables
        , worklists
        , permissions
        , scripts
        , description
        , manager_bypass
        , creation_guard
        ) = wfdc.parseWorkflowXML(body, encoding)

        _initDCWorkflow( wf
                       , title
                       , description
                       , manager_bypass
                       , creation_guard
                       , state_variable
                       , initial_state
                       , states
                       , transitions
                       , variables
                       , worklists
                       , permissions
                       , scripts
                       , portal     # not sure what to pass here
                                    # the site or the wft?
                                    # (does it matter at all?)
                      )
        logger.info("Added workflow %s" % wf_id)


def restorePloneTool(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    tool = getToolByName(portal, "plone_utils")
    if tool.meta_type == 'PlonePAS Utilities Tool':
        from Products.CMFPlone.PloneTool import PloneTool

        # PloneSite has its own security check for manage_delObjects which
        # breaks in the test runner. So we bypass this check.
        super(portal.__class__, portal).manage_delObjects(['plone_utils'])
        portal._setObject(PloneTool.id, PloneTool())
        logger.info("Replaced obsolete PlonePAS version of plone tool "
                    "with the normal one.")


def updateImportStepsFromBaseProfile(context):
    """Updates the available import steps for existing sites."""
    context.setBaselineContext("profile-%s" % _DEFAULT_PROFILE)

