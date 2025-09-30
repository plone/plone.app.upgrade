from plone.registry.interfaces import IRegistry
from zope.component import getUtility


def update_tinymce_toolbar_menu_styles(context):
    registry = getUtility(IRegistry)

    # rename "styleselect" to "styles"
    mce_toolbar = registry.records["plone.toolbar"].value
    registry.records["plone.toolbar"] = mce_toolbar.replace("styleselect", "styles")

    # rename "formats" to "styles"
    mce_menu = registry.records["plone.menu"].value
    mce_menu["format"]["items"] = mce_menu["format"]["items"].replace(
        "formats", "styles"
    )
    registry.records["plone.menu"] = mce_menu
