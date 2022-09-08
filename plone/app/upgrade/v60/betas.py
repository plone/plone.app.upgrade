from Products.CMFCore.Expression import Expression
from Products.CMFPlone.utils import getToolByName

import logging


logger = logging.getLogger("plone.app.upgrade")


def add_the_timezone_property(context):
    """Ensure that the portal_memberdata tool has the timezone property."""
    portal_memberdata = getToolByName(context, "portal_memberdata")
    if portal_memberdata.hasProperty("timezone"):
        return
    portal_memberdata.manage_addProperty("timezone", "", "string")


def add_action_icons(context):
    """Add action icons"""
    portal_actions = getToolByName(context, "portal_actions")

    def _set_icon_expr(action, icon_expr):
        """setting icon_expr also requires to add an icon_expr_object"""
        action.icon_expr = icon_expr
        action.icon_expr_object = Expression(icon_expr)

    # Fix actions that had an icon expression
    for action_path, old, new in (
        (
            "document_actions/print",
            "string:$portal_url/print_icon.png",
            "string:plone-print",
        ),
        ("document_actions/rss", "string:$portal_url/rss.png", "string:plone-rss"),
    ):
        action = portal_actions.unrestrictedTraverse(action_path, None)
        if action is not None:
            if action.icon_expr == old:
                _set_icon_expr(action, new)
            elif action.icon_expr != new:
                logger.info("Skipping action %r, it looks customized", action_path)

    # Fix actions that did not have an icon expression
    mapping = {
        "object_buttons/copy": "string:plone-copy",
        "object_buttons/cut": "string:plone-cut",
        "object_buttons/delete": "string:plone-delete",
        "object_buttons/ical_import_disable": "",
        "object_buttons/ical_import_enable": "",
        "object_buttons/paste": "string:plone-paste",
        "object_buttons/redirection": "string:plone-redirection",
        "object_buttons/rename": "string:plone-rename",
        "object/contentrules": "string:plone-rules",
        "object/folderContents": "string:toolbar-action/folderContents",
        "object/history": "string:toolbar-action/history",
        "object/ical_import_settings": "",
        "object/local_roles": "string:toolbar-action/sharing",
        "object/syndication": "string:plone-rss",
        "portal_tabs/index_html": "string:plone-home",
        "site_actions/accessibility": "string:plone-accessibility",
        "site_actions/contact": "string:plone-contact-info",
        "site_actions/sitemap": "string:plone-sitemap",
        "user/dashboard": "string:plone-dashboard",
        "user/join": "string:plone-register",
        "user/login": "string:plone-login",
        "user/logout": "string:plone-logout",
        "user/plone_setup": "string:plone-controlpanel",
        "user/preferences": "string:plone-user",
        "user/undo": "string:plone-undo",
    }
    for action_path, new in mapping.items():
        action = portal_actions.unrestrictedTraverse(action_path, None)
        if action:
            if not action.icon_expr:
                _set_icon_expr(action, new)
            elif action.icon_expr != new:
                logger.info("Skipping action %r, it looks customized", action_path)


def rename_dexteritytextindexer_behavior(context):
    """Rename collective.dexteritytextindexer behavior to plone.textindexer"""
    portal_types = getToolByName(context, "portal_types")

    # Gather the FTIs that have the obsolete behavior,
    # it can appear with the name or the interface identifier
    old_behaviors = {
        "collective.dexteritytextindexer",
        "collective.dexteritytextindexer.behavior.IDexterityTextIndexer",
    }
    ftis_to_fix = (
        fti
        for fti in portal_types.objectValues("Dexterity FTI")
        if set(fti.behaviors) & old_behaviors
    )

    for fti in ftis_to_fix:
        # Rename the behavior
        behaviors = [
            "plone.textindexer" if behavior in old_behaviors else behavior
            for behavior in fti.behaviors
        ]

        # Ensure we did not have the behavior more than once
        while behaviors.count("plone.textindexer") > 1:
            behaviors.remove("plone.textindexer")

        # Set the updated behaviors
        fti.behaviors = tuple(behaviors)
