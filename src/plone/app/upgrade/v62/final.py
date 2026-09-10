from plone.base.interfaces.controlpanel import IImagingSchema
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import logging

logger = logging.getLogger(__name__)


def update_iimagingschema_fields(context):
    # Allow the `sizes` attribute in `sourceset` of picture_variants in
    # `IImagingSchema`
    # The `IImagingSchema` picture_variants JSON field's schema was updated
    # with a `sizes` attribute for the `sourceset` array of objects. This
    # upgrade step updates the schema to allow the `sizes` attribute.

    registry = getUtility(IRegistry)

    # re-register the schema in the registry
    registry.registerInterface(IImagingSchema, prefix="plone")
    logger.info("Imaging: Updated the control panel schema fields.")

    # Also add the `sizes` attribute for the `small` picture variant, if it is
    # still the default value.
    picture_variants = registry.records["plone.picture_variants"].value

    # Checking if the `small` variant is still the default.
    sourceset = picture_variants.get("small", {}).get("sourceset", [])

    if (
        len(sourceset) == 1
        and sourceset[0]["scale"] == "preview"
        and len(sourceset[0]["additionalScales"]) == 2
        and "large" in sourceset[0]["additionalScales"]
        and "larger" in sourceset[0]["additionalScales"]
        and "sizes" not in sourceset[0]
    ):
        sourceset[0][
            "sizes"
        ] = "(min-width: 576px) 400px, (min-width: 768px) 600px, 98vw"

        picture_variants["small"]["sourceset"] = sourceset
        logger.info("Imaging: Added the sizes attribute to the small picture variant.")

    else:
        logger.info(
            "Imaging: Did not add the sizes attribute to the small picture variant, "
            "because the plone.picture_variants value has been customized."
        )
