from plone.base.interfaces.controlpanel import IImagingSchema
from plone.registry.interfaces import IRegistry
from zope.component import getUtility


def update_iimagingschema_fields(context):
    # Allow the `sizes` attribute in `sourceset` of picture_variants in `IImagingSchema`
    # The `IImagingSchema` picture_variants JSON field's schema was updated
    # with a `sizes` attribute for the `sourceset` array of objects. This
    # upgrade step updates the schema to allow the `sizes` attribute.

    registry = getUtility(IRegistry)

    # re-register the schema in the registry
    registry.registerInterface(IImagingSchema, prefix="plone")
