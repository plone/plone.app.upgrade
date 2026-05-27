from plone.browserlayer.interfaces import ILocalBrowserLayerType
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from zope.component import getAllUtilitiesRegisteredFor
from zope.component import getSiteManager
from zope.publisher.interfaces.browser import IBrowserRequest
import json
import logging


logger = logging.getLogger(__name__)


def remove_portal_view_customizations(context):
    # If the plone.app.customerize package is still available, do nothing.
    isAvailable = True
    try:
        from five.customerize.zpt import TTWViewTemplateRenderer
    except ImportError:
        isAvailable = False
    if isAvailable:
        logger.info("plone.app.customerize is still installed. Skipping removal of portal_view_customizations.")
        return

    # Else, if the portal_view_customizations tool actually has
    #   customisations, stop the upgrade with an error.
    if hasLocalViewCustomizations(context):
        raise Exception("Portal view customizations are still present. Please remove them manually before continuing.")

    # Else, if the portal_view_customizations tool is empty, remove it.
    from plone.app.upgrade.utils import cleanUpToolRegistry
    portal_url = getToolByName(context, "portal_url")
    portal = portal_url.getPortalObject()
    portal._delObject("portal_view_customizations")
    cleanUpToolRegistry(context)


def hasLocalViewCustomizations(context):
    try:
        from five.customerize.zpt import TTWViewTemplateRenderer
        from five.customerize.interfaces import ITTWViewTemplate
    except ImportError:
        return False

    layers = getAllUtilitiesRegisteredFor(ILocalBrowserLayerType)
    components = getSiteManager(context)
    for reg in components.registeredAdapters():
        if (
            len(reg.required) in (2, 4, 5)
            and (
                reg.required[1].isOrExtends(IBrowserRequest)
                or reg.required[1] in layers
            )
            and ITTWViewTemplate.providedBy(reg.factory)
        ):
            return True