from plone.base.interfaces import ITinyMCESchema
from plone.base.utils import get_installer
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import json
import logging
import re

logger = logging.getLogger(__name__)


def update_tinymce_toolbar_menu_styles(context):
    registry = getUtility(IRegistry)

    # rename "styleselect" to "styles"
    mce_toolbar = registry.records["plone.toolbar"].value
    registry["plone.toolbar"] = mce_toolbar.replace("styleselect", "styles")

    # rename "formats" to "styles"
    mce_menu = json.loads(registry.records["plone.menu"].value)

    try:
        mce_menu["format"]["items"] = mce_menu["format"]["items"].replace(
            "formats", "styles"
        )
        registry["plone.menu"] = json.dumps(mce_menu, indent=4)
    except KeyError:
        # in case of a custom tinymce menu configuration
        logger.info(
            "Could not rename 'formats' to 'styles' in 'plone.menu' registry value due to custom TinyMCE menu configuration"
        )


def add_tinymce_license_key(context):
    registry = getUtility(IRegistry)
    # re-register the interface with prefix, needed for plone.license_key
    registry.registerInterface(ITinyMCESchema, prefix="plone")


def install_plone_app_layout(context):
    """Install plone.app.layout if the current site has the classic distribution."""
    try:
        from plone.distribution.api.distribution import get_current_distribution
    except ImportError:
        return

    dist = get_current_distribution()
    if dist is None or dist.name != "classic":
        return
    installer = get_installer(context)
    if installer.is_product_installed("plone.app.layout"):
        return
    installer.install_product("plone.app.layout")


def cleanup_resource_registry(self):
    """Remove remaining deprecated Plone 5 resource registry records."""
    # Regex for deprecated resource registry keys.
    resource_regex = re.compile(
        r"plone.bundles.*("
        "compile|"
        "develop_css|"
        "develop_javascript|"
        "last_compilation|"
        "merge_with|"
        "resources|"
        "stub_js_modules"
        ")"
    )
    registry = getUtility(IRegistry)

    # Create a static list of registry keys to not operate on a live iterator
    # which changes size when deleting keys.
    keys = list(registry.records.keys())
    for key in keys:
        # Remove "plone.resources", "plone.lessvariables" and deprecated bundle keys.
        if (
            "plone.resources" == key[:15]
            or key == "plone.lessvariables"
            or resource_regex.match(key)
        ):
            del registry.records[key]
            logger.info("Removed deprecated registry record %s.", key)
