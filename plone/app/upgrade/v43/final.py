import logging
from Products.CMFCore.utils import getToolByName

from zope.component import queryUtility
from plone.contentrules.engine.interfaces import IRuleStorage
from plone.contentrules.engine.assignments import check_rules_with_dotted_name_moved

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
    qi = getToolByName(context, 'portal_quickinstaller')
    qi.upgradeProduct('plone.app.querystring')


def improveSyndication(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v43:to435')
