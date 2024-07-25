from Products.CMFCore.utils import getToolByName

import logging


logger = logging.getLogger(__name__)


def remove_portal_properties_tool(context):
    """Remove the portal_properties tool.

    Core Plone has moved to the configuration registry in Plone 5.0.
    Add-ons may have still used it, but we announced we would remove
    it in Plone 6.1.
    """
    portal = getToolByName(context, "portal_url").getPortalObject()
    tool = getattr(portal, "portal_properties", None)
    if tool is None:
        return
    # portal._delObject("portal_properties") would give:
    # AttributeError: 'PropertiesTool' object has no attribute '__of__'
    portal._delOb("portal_properties")
    logger.info("Removed portal_properties tool.")
