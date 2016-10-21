import logging
from Products.CMFCore.utils import getToolByName

from zope.component import getAllUtilitiesRegisteredFor
from zope.component import queryUtility
from plone.contentrules.engine.interfaces import IRuleStorage
from plone.contentrules.engine.assignments import \
    check_rules_with_dotted_name_moved

from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.utils import unregisterSteps
from plone.app.upgrade.v43.alphas import upgradeTinyMCEAgain

# We had our own version of this, but it was just a copy.  We keep a
# reference here to avoid breakage if someone imports it.
upgradeTinyMCEAgain  # Pyflakes
logger = logging.getLogger('plone.app.upgrade')


def addScalingQualitySetting(context):
    """Add 'quality' to portal_properties.imaging_properties"""
    sptool = getToolByName(context, 'portal_properties')
    # handle plone5-tests (plone.app.imaging does not set imaging_properties)
    if getattr(sptool, 'imaging_properties', None):
        imaging_properties = sptool.imaging_properties
        if not imaging_properties.hasProperty('quality'):
            if 'quality' in imaging_properties.__dict__:
                # fix bug if 4.3.1 pending has been tested
                del imaging_properties.quality
            imaging_properties.manage_addProperty('quality', 88, 'int')
            logger.log(logging.INFO,
                       "Added 'quality' property to imaging_properties.")


def upgradeContentRulesNames(context):
    storage = queryUtility(IRuleStorage)
    for key in storage.keys():
        check_rules_with_dotted_name_moved(storage[key])


def removePersistentKSSMimeTypeImportStep(context):
    unregisterSteps(context, import_steps=['kss_mimetype'])


def addDefaultPlonePasswordPolicy(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    from Products.PlonePAS.Extensions.Install import setupPasswordPolicyPlugin
    setupPasswordPolicyPlugin(portal)


def addShowInactiveCriteria(context):
    qi = getToolByName(context, 'portal_quickinstaller', None)
    if qi is not None:
        qi.upgradeProduct('plone.app.querystring')


def improveSyndication(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v43:to435')


def unmarkUnavailableProfiles(context):
    """Unmark installed profiles that are no longer available.
    """
    setup = context
    available = [profile['id'] for profile in setup.listProfileInfo()]
    for profile_id in setup._profile_upgrade_versions.copy():
        if profile_id in available:
            continue
        logger.info('Setting installed version of profile %s as unknown.',
                    profile_id)
        setup.unsetLastVersionForProfile(profile_id)


def markProductsInstalledForUninstallableProfiles(context):
    """Cleanup uninstalled products.

    QI 3.0.8 (Plone 4.3.5 / 5.0b1) no longer prevents INonInstallable
    profiles from being recorded as QI installed products, because
    really they are auto-installed products, not non-installable ones.

    This means we should do some migration.

    Go through all INonInstallable profiles, check if the profile was
    applied and mark it as installed in QI.  This might mark too many
    of these as installed, but so be it.

    But: there are also INonInstallable products.  These are ignored
    by the QI events.  So if the non installable profile of a non
    installable product gets applied, the product is still NOT marked
    as installed in the QI.  So we should not do that here either, but
    that goes fine because we use the same logic.

    In Plone 5.0, these packages fall under both categories:

    [
    'Archetypes',
    'CMFDiffTool',
    'CMFEditions',
    'CMFFormController',
    'CMFPlone',
    'CMFQuickInstallerTool',
    'MimetypesRegistry',
    'NuPlone',
    'PasswordResetTool',
    'PloneLanguageTool',
    'PlonePAS',
    'PortalTransforms',
    'borg.localrole',
    'plone.app.blob',
    'plone.app.collection',
    'plone.app.dexterity',
    'plone.app.discussion',
    'plone.app.event',
    'plone.app.folder',
    'plone.app.imaging',
    'plone.app.querystring',
    'plone.app.registry',
    'plone.app.theming',
    'plone.formwidget.recurrence',
    'plone.keyring',
    'plone.outputfilters',
    'plone.portlet.collection',
    'plone.portlet.static',
    'plone.protect',
    'plone.resource',
    ]

    These only fall under non installable profiles:

    [
    'plone.app.contenttypes',
    'plone.app.multilingual',
    'plone.app.versioningbehavior',
    'plone.browserlayer',
    ]

    BTW, plone.browserlayer does not even have a profile...

    These only fall under non installable products:

    [
    'CMFDefault',
    'CMFPlone.migrations',
    'CMFTopic',
    'CMFUid',
    'DCWorkflow',
    'plone.app.caching',
    'plone.app.intid',
    'plone.app.referenceablebehavior',
    'plone.app.relationfield',
    'plone.app.upgrade.v40',
    'plone.app.upgrade.v41',
    'plone.app.upgrade.v42',
    'plone.app.upgrade.v43',
    'plone.app.widgets',
    'plone.app.z3cform',
    'plonetheme.barceloneta',
    'wicked.at',
    ]
    """
    from Products.CMFPlone.interfaces import INonInstallable
    setup = context
    qi = getToolByName(context, 'portal_quickinstaller', None)
    if qi is None:
        return
    # Get list of profiles that are marked as not installable.
    profile_ids = []
    utils = getAllUtilitiesRegisteredFor(INonInstallable)
    for util in utils:
        profile_ids.extend(util.getNonInstallableProfiles())
    # If non installable profiles (really: hidden profiles) have been
    # installed in GS, mark their products as installed in the QI.
    for profile_id in profile_ids:
        if setup.getLastVersionForProfile(profile_id) == 'unknown':
            # not installed
            continue
        # Profile was installed.  Mark its corresponding product as
        # installed too.
        try:
            profile = setup.getProfileInfo(profile_id)
        except KeyError:
            # Profile was installed at some point, but is no longer
            # available.  Should have been caught by the
            # unmarkUnavailableProfiles upgrade step, but let's be
            # careful.
            continue
        product_id = profile['product']
        if qi.isProductInstalled(product_id):
            # all is well
            continue
        version = qi.getProductVersion(product_id)
        qi.notifyInstalled(
            product_id,
            locked=False,
            logmsg="Marked as installed by plone.app.upgrade",
            settings={},
            installedversion=version,
            status='installed',
            error=False,
        )


def cleanupUninstalledProducts(context):
    """Cleanup uninstalled products.

    QI 3.0.7 (Plone 4.3.4 / 5.0a3) removes the InstalledProduct
    instance when a product is uninstalled, because leaving the
    instance around can prevent settings from being stored properly
    on subsequent installation of the product.

    QI 3.0.12 (unreleased, maybe Plone 4.3.7 / 5.0rc3), marks
    install profiles as unknown when uninstalling a product, so
    portal_setup also regards it as not installed.

    This means we should do some migration.

    Go through all InstalledProduct items in the QI and remove any
    that are not installed.  And unset their last profile versions in
    GS too.
    """
    setup = context
    qi = getToolByName(context, 'portal_quickinstaller', None)
    if qi is None:
        return
    for prod in qi.objectValues():
        if prod.isInstalled():
            continue
        product_id = prod.id
        qi.manage_delObjects(product_id)
        profile = qi.getInstallProfile(product_id)
        if profile is None:
            continue
        # Mark profile as uninstalled/unknown.
        profile_id = profile['id']
        setup.unsetLastVersionForProfile(profile_id)


def removeFakeKupu(context):
    """Remove fake kupu tool and related settings and resources.

    plone.app.upgrade has a fake kupu tool class that is used when the
    Products.kupu package is not available.  This is a minimal working
    tool, so stuff does not break before we have had a chance to clean
    it up.

    This fake kupu tool may be left behind, even when you have cleanly
    uninstalled kupu beforehand.

    So we remove the fake tool and remove related settings and
    resources.

    When Products.kupu is available as package, we do nothing: someone
    may actually still use kupu and it may actually still work.
    """
    kupu_id = 'kupu_library_tool'
    portal = getToolByName(context, 'portal_url').getPortalObject()
    if kupu_id not in portal:
        return
    from plone.app.upgrade.kupu_bbb import PloneKupuLibraryTool
    kupu_tool = portal[kupu_id]
    if not isinstance(kupu_tool, PloneKupuLibraryTool):
        # The real kupu is available.  Keep it.
        return
    portal._delObject(kupu_id)
    logger.info('Removed fake %s', kupu_id)
    # Some other stuff may be there when kupu was not cleanly
    # uninstalled.
    # Remove resources that want kupu enabled.
    bad_expr = 'python:portal.kupu_library_tool.isKupuEnabled'
    tool_ids = ('portal_css', 'portal_javascripts', 'portal_kss')
    for tool_id in tool_ids:
        tool = getToolByName(portal, tool_id, None)
        if tool is None:
            continue
        resources = tool.getResourcesDict()
        for resource_id, resource in resources.items():
            expression = resource.getExpression()
            if expression.startswith(bad_expr):
                tool.unregisterResource(resource_id)
                logger.info('Removed %s from %s.', resource_id, tool_id)
            elif kupu_id in expression:
                # We are tempted to remove this, but who knows if the
                # expression is something like this:
                # "'kupu_library_tool' not in portal"
                logger.warn('%s in %s has %s in expression. You probably '
                            'want to change the expression or remove the '
                            'resource.', resource_id, tool_id, kupu_id)
    # Remove control panel.
    control_panel = getToolByName(portal, 'portal_controlpanel', None)
    if control_panel is not None:
        # Note that this does nothing when the configlet is not there.
        control_panel.unregisterConfiglet('kupu')
        logger.info('Removed kupu control panel configlet.')
    # Remove editor from site_properties.
    pprops = getToolByName(portal, 'portal_properties', None)
    available_editors = []
    if pprops is not None:
        site_properties = getattr(pprops, 'site_properties', None)
        if site_properties is not None:
            available_editors = list(
                site_properties.getProperty('available_editors', []))
            if 'Kupu' in available_editors:
                available_editors.remove('Kupu')
                site_properties._updateProperty(
                    'available_editors', tuple(available_editors))
                logger.info('Removed Kupu from available_editors.')
            if site_properties.getProperty('default_editor') == 'Kupu':
                if 'TinyMCE' in available_editors:
                    site_properties._updateProperty('default_editor',
                                                    'TinyMCE')
                    logger.info('Changed default editor to TinyMCE.')
                else:
                    site_properties._updateProperty('default_editor', '')
                    logger.info('Changed default editor to basic.')
    # Remove from portal_memberdata.  Note that you can use
    # collective.setdefaulteditor if you want more options, like
    # updating the chosen editor for all existing members.
    member_data = getToolByName(context, 'portal_memberdata')
    if member_data.getProperty('wysiwyg_editor') == 'Kupu':
        member_data._updateProperty('wysiwyg_editor', '')
        logger.info('Changed new member wysiwyg_editor to site default.')


def addSortOnProperty(context):
    """Add sort_on field to search controlpanel.
    
    The default value of this field is relevance.
    """
    site_properties = getToolByName(context, 'portal_properties').site_properties
    if not site_properties.hasProperty('sort_on'):
        if 'sort_on' in site_properties.__dict__:
            # fix bug if 4.3.1 pending has been tested
            del site_properties.sort_on
        site_properties.manage_addProperty('sort_on', 'relevance', 'string')
        logger.log(logging.INFO,
                   "Added 'sort_on' property to site_properties.")
