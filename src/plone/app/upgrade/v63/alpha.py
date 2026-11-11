from plone.base.interfaces import IImagingSchema
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import logging

logger = logging.getLogger(__name__)

NEW_SIZES = ["qhd 2560:65536", "fullhd 1920:65536"]


def update_imaging_settings(context):
    """Add the scale format setting, and the scales fullhd and qhd."""
    registry = getUtility(IRegistry)
    # Adds plone.scale_format, keeping the values of the other records.
    registry.registerInterface(IImagingSchema, prefix="plone")
    logger.info("Imaging: added the setting for the format of scaled images.")

    record = registry.records["plone.allowed_sizes"]
    sizes = list(record.value or [])
    names = {line.split()[0] for line in sizes if line.strip()}
    widths = {line.split()[-1].split(":")[0] for line in sizes if ":" in line}
    added = [
        line
        for line in NEW_SIZES
        if line.split()[0] not in names and line.split()[-1].split(":")[0] not in widths
    ]
    if added:
        record.value = added + sizes
        logger.info("Imaging: added the scales %s.", ", ".join(added))
