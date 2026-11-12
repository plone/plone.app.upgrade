from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import logging

logger = logging.getLogger(__name__)

NEW_SIZES = ["qhd 2560:65536", "fullhd 1920:65536"]
OLD_LARGE_SCALES = ["preview", "teaser", "large", "great", "huge"]


def add_larger_image_scales(context):
    """Add the image scales fullhd and qhd.

    A scale is not added when the site already has a scale with that name or
    width. The scales are added to the ``large`` picture variant only when it
    still has its default scales.
    """
    registry = getUtility(IRegistry)

    record = registry.records.get("plone.allowed_sizes")
    if record is None:
        return
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
        logger.info("Added the image scales %s.", ", ".join(added))

    names = {line.split()[0] for line in record.value if line.strip()}
    variants = registry.get("plone.picture_variants")
    try:
        source = variants["large"]["sourceset"][-1]
    except (TypeError, KeyError, IndexError):
        return
    if source.get("additionalScales") != OLD_LARGE_SCALES:
        return
    if not {"fullhd", "qhd"} <= names:
        return
    variants = dict(variants)
    large = dict(variants["large"])
    sourceset = list(large["sourceset"])
    sourceset[-1] = dict(source, additionalScales=OLD_LARGE_SCALES + ["fullhd", "qhd"])
    large["sourceset"] = sourceset
    variants["large"] = large
    registry["plone.picture_variants"] = variants
    logger.info("Added the image scales fullhd and qhd to the picture variant large.")
