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


def update_srcset_picture_variants(context):
    # We have modified the value of the default `srcset` attribute that we are providing
    # in the `small` image scale.
    # In this upgrade step we will try to upgrade such value.
    # We will only upgrade the sites that keep the default value for the picture variants
    # configuration. In other cases, we just the registry entry untouch because the user
    # has modified the setting
    registry = getUtility(IRegistry)

    current_picture_variants = registry.records["plone.picture_variants"].value

    # This is the old default value
    old_picture_variants = {
        "large": {
            "title": "Large",
            "sourceset": [
                {
                    "scale": "larger",
                    "additionalScales": [
                        "preview",
                        "teaser",
                        "large",
                        "great",
                        "huge",
                    ],
                },
            ],
        },
        "medium": {
            "title": "Medium",
            "sourceset": [
                {
                    "scale": "teaser",
                    "additionalScales": ["preview", "large", "larger", "great"],
                },
            ],
        },
        "small": {
            "title": "Small",
            "sourceset": [
                {
                    "scale": "preview",
                    "additionalScales": ["large", "larger"],
                    "sizes": "(min-width: 576px) 400px, (min-width: 768px) 600px, 98vw",
                },
            ],
        },
    }

    if current_picture_variants == old_picture_variants:
        # Let's change the value of the `sizes` attribute for the `small` size

        # Checking if the `small` variant is still the default.
        sourceset = current_picture_variants.get("small", {}).get("sourceset", [])
        sourceset[0][
            "sizes"
        ] = "(min-width: 768px) 600px, (min-width: 576px) 400px, 98vw"

        current_picture_variants["small"]["sourceset"] = sourceset
        logger.info(
            "Imaging: Modified the sizes attribute of the small picture variant."
        )
    else:
        logger.info(
            "Imaging: The picture variants configuration is not the default one. Nothing done."
        )
