import logging
from Products.CMFCore.utils import getToolByName


logger = logging.getLogger('plone.app.upgrade')


def addScalingQualitySetting(context):
    """Add 'quality' to portal_properties.imaging_properties"""
    sptool = getToolByName(context, 'portal_properties')
    imaging_properties = sptool.imaging_properties
    if not imaging_properties.hasProperty('quality'):
        imaging_properties.manage_addProperty('quality', 88, 'int')
        logger.log(logging.INFO,
                   "Added 'quality' property to imaging_properties.")
