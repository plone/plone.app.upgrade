from Products.CMFPlone.utils import getToolByName
import logging

logger = logging.getLogger("plone.app.upgrade")


def add_the_timezone_property(context):
    """Ensure that the portal_memberdata tool has the timezone property."""
    portal_memberdata = getToolByName(context, "portal_memberdata")
    if portal_memberdata.hasProperty("timezone"):
        return
    portal_memberdata.manage_addProperty("timezone", "", "string")
