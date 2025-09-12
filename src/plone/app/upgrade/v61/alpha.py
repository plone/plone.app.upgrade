from plone.base.interfaces.controlpanel import IFilterSchema
from plone.base.interfaces.controlpanel import ITinyMCEPluginSchema
from plone.registry.interfaces import IRegistry
from zope.component import getUtility


def add_feature_tinymce_accordion_plugin(context):
    # add accordion plugin to tinymce plugins
    # it's not enabled per default in the registry

    registry = getUtility(IRegistry)

    # save the old values temporarily
    plugins_record = registry.records.get("plone.plugins")
    valid_tags_record = registry.records.get("plone.valid_tags")
    custom_attributes_record = registry.records.get("plone.custom_attributes")

    old_value_plugins = plugins_record.value
    old_value_valid_tags = valid_tags_record.value
    old_value_custom_attributes = custom_attributes_record.value

    # delete the old registry record, it holds the wrong vocabulary of the old schema
    del registry.records["plone.plugins"]
    del registry.records["plone.valid_tags"]
    del registry.records["plone.custom_attributes"]

    # re-register the schema in the registry
    registry.registerInterface(ITinyMCEPluginSchema, prefix="plone")
    registry.registerInterface(IFilterSchema, prefix="plone")

    # add the old value for plugin
    plugins_record = registry.records.get("plone.plugins")
    plugins_record.value = old_value_plugins

    # add the old value for valid_tags
    valid_tags_record = registry.records.get("plone.valid_tags")
    for val in old_value_valid_tags:
        if val in valid_tags_record.value:
            continue
        valid_tags_record.value.append(val)

    # add the old value for custom_attributes
    custom_attributes_record = registry.records.get("plone.custom_attributes")
    for val in old_value_custom_attributes:
        if val in custom_attributes_record.value:
            continue
        custom_attributes_record.value.append(val)
