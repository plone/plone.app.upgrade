from Acquisition import aq_parent
from Products.CMFCore.utils import getToolByName

import logging


logger = logging.getLogger(__name__)


def remove_empty_portal_properties(context):
    """Remove the portal_properties tool if it is empty.

    Remove any property sheet in it that is empty.
    Core Plone has moved to the configuration registry in Plone 5.0.
    Add-ons may have still used it, but it is scheduled for
    removal in Plone 6.1.
    We might still keep the class.  Let's see.
    """
    tool = getToolByName(context, "portal_properties", None)
    if tool is None:
        return
    logger.info("Checking sheets in portal_properties tool.")
    # Get all names first.  I don't want to iterate over a list
    # and at the same time delete items from that list.
    names = list(tool.objectIds())
    for name in names:
        sheet = tool[name]
        properties = sheet.propertyIds()
        if len(properties) > 1:
            logger.info(
                "Keeping portal_properties.%s: it has %d properties.",
                name,
                len(properties),
            )
            continue
        if properties[0] != "title":
            logger.info(
                "Keeping portal_properties.%s: it has a property '%s'.",
                name,
                properties[0],
            )
            continue
        tool._delObject(name)
        logger.info("Removed empty portal_properties.%s.", name)

    # Check if any sheets are left.
    if tool.objectIds():
        logger.info(
            "Keeping portal_properties, as it still has these sheets: %s.",
            ", ".join(tool.objectIds()),
        )
        return
    parent = aq_parent(tool)
    parent._delObject("portal_properties")
    logger.info("Removed empty portal_properties tool.")
