from plone.base.interfaces import IImagingSchema
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import logging

logger = logging.getLogger(__name__)


def add_avif_imaging_settings(context):
    # IImagingSchema got avif_mode, avif_quality and avif_speed.
    registry = getUtility(IRegistry)
    registry.registerInterface(IImagingSchema, prefix="plone")
    logger.info("Imaging: Registered the AVIF settings.")
