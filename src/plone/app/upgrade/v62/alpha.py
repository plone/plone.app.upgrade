from plone.base.interfaces import ITinyMCESchema
from plone.base.utils import get_installer
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility

import json
import logging

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


def fix_history_action_permission(context):
    """Change history action permission to CMFEditions: Access previous versions.

    Fixes: https://github.com/plone/Products.CMFPlone/issues/4059
    """
    portal_actions = getToolByName(context, "portal_actions")
    action = portal_actions.unrestrictedTraverse("object/history", None)
    if action is None:
        logger.info("Action object/history does not exist, nothing to do.")
        return
    old_perm = ("Modify portal content",)
    new_perm = ("CMFEditions: Access previous versions",)
    if action.permissions == new_perm:
        return
    if action.permissions != old_perm:
        logger.info("Action object/history has customized permissions, not changing.")
        return
    action.permissions = new_perm


def add_s_to_valid_tags(context):
    """Add <s> tag to valid_tags for TinyMCE strikethrough support.

    TinyMCE 8 uses <s> for strikethrough, but <s> was not in the default
    valid_tags list, causing strikethrough formatting to be silently stripped.

    Fixes: https://github.com/plone/Products.CMFPlone/issues/3069
    """
    registry = getUtility(IRegistry)
    record = registry.records.get("plone.valid_tags")
    if record is None:
        return
    if "s" not in record.value:
        record.value = sorted([*record.value, "s"])
