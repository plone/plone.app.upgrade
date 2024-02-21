from AccessControl.Permission import Permission
from plone.base.utils import get_installer
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility
from zope.component.hooks import getSite

import logging


logger = logging.getLogger(__name__)
SITE_ADMIN = "Site Administrator"
SITE_ADMIN_PERMISSIONS = [
    "Inspect Relations",
    "Plone Site Setup: Editing",
    "Plone Site Setup: Filtering",
    "Plone Site Setup: Language",
    "Plone Site Setup: Mail",
    "Plone Site Setup: Markup",
    "Plone Site Setup: Navigation",
    "Plone Site Setup: Overview",
    "Plone Site Setup: Search",
    "Plone Site Setup: Security",
    "Plone Site Setup: Site",
    "Plone Site Setup: Themes",
    "Plone Site Setup: TinyMCE",
    "Plone Site Setup: Types",
    "Plone Site Setup: Users and Groups",
]


def rolemap_site_admin(context):
    """Add Site Administrator role to various permissions.

    Especially for control panels, permissions were defined in Python or zcml
    with both Manager and Site Administrator in the roles.
    On startup, this is set on the Zope level, NOT the Plone level.
    And on the Zope level the Site Administrator role is not defined.
    This works, but can give problems.
    So setting the Site Administrator role was moved to rolemap.xml
    See https://github.com/plone/Products.CMFPlone/pull/3225

    That works for new sites, but migrated sites now had a problem.
    Site Administrators lost all those permissions, and could not even
    see the Site Setup.  How to fix that?  Here we more or less follow this plan:
    https://github.com/plone/Products.CMFPlone/pull/3225#issuecomment-1467095416
    Not entirely though.  What we do for real, is described in inline comments below.
    """
    portal = getSite()
    for perm in portal.ac_inherited_permissions(1):
        # perm is a tuple: name, value, inherited roles.
        # ('Plone Site Setup: Editing', (), ('Manager',))
        name, value = perm[:2]
        for permission in SITE_ADMIN_PERMISSIONS:
            if name == permission:
                perm = Permission(name, value, portal)
                # getRoles gives the roles set on the current level (Plone),
                # so not inherited from Zope.
                # Note: when nothing is set explicitly, you still get ['Manager'].
                roles = perm.getRoles()
                if SITE_ADMIN in roles:
                    # nothing to do
                    continue
                # If roles is a list, then it is acquired.
                # It roles is a tuple, then it is not acquired.
                # If the permission is NOT acquired, this means that the user
                # has explicitly switched this off.  We leave it alone then.
                acquired = isinstance(roles, list)
                if acquired:
                    # This is the main thing we want to change:
                    # add Site Administrator to the roles on Plone level.
                    roles.append(SITE_ADMIN)
                    perm.setRoles(roles)
                    logger.info("Added %s role to '%s' permission.", SITE_ADMIN, name)


def fix_iterate_profiles(context):
    """Fix profiles of plone.app.iterate.

    See https://github.com/plone/plone.app.iterate/issues/99
    There used to be only a plone.app.iterate:plone.app.iterate profile.
    This was kept for backwards compatibility, but copied to a
    plone.app.iterate:default profile, as is usual.
    We want to remove the old profile definition, but this might give problems
    when someone still has this installed instead of the default profile.

    Later we may want to do something similar with CMFPlacefulWorkflow:
    https://github.com/plone/Products.CMFPlacefulWorkflow/issues/38
    But this has no default profile yet.
    """
    product = "plone.app.iterate"
    old_profile = "plone.app.iterate:plone.app.iterate"
    installer = get_installer(context)

    # check the product
    product_installed = installer.is_product_installed("plone.app.iterate")
    if product_installed:
        logger.info("The %s product is currently installed.", product)
    else:
        logger.info("The %s product is currently not installed.", product)

    # check the old profile
    old_profile_installed = installer.is_profile_installed(old_profile)
    if old_profile_installed:
        logger.info("The old %s profile is currently installed.", old_profile)
    else:
        logger.info("The old %s profile is currently not installed.", old_profile)

    if not (product_installed or old_profile_installed):
        logger.info("%s is not installed at all, nothing needs to be done.", product)
        return

    if old_profile_installed:
        # mark as not installed
        context.unsetLastVersionForProfile(old_profile)
    if not product_installed:
        # This is the main fix: the old profile was marked as installed,
        # so now the new profile should be installed.
        installer.install_product(product)
    else:
        # Now seems a good time to run any upgrade steps.
        installer.upgrade_product(product)


def fix_tinymce_menubar(context):
    """Fix menubar with 'toolsview' instead of 'tools' and 'view'.

    See https://github.com/plone/Products.CMFPlone/issues/3785
    """
    registry = getUtility(IRegistry)
    record = registry.records.get("plone.menubar")
    if record is None:
        return
    value = record.value
    if "toolsview" not in value:
        return
    index = value.index("toolsview")
    value.pop(index)
    value.insert(index, "view")
    value.insert(index, "tools")
    record.value = value


def fix_syndication_settings(context):
    """Fix Syndication Setting in the registry
    Products.CMFPlone.interfaces.syndication.ISiteSyndicationSettings
    is moved to plone.base.interfaces.syndication.ISiteSyndicationSettings.

    See https://github.com/plone/Products.CMFPlone/issues/3805
    """
    try:
        from plone.base.interfaces.syndication import ISiteSyndicationSettings
    except ImportError:
        # Upgrade step called from older Plone version?
        return

    registry = getUtility(IRegistry)
    record_keys = list(registry.records.keys())
    portal_catalog = getToolByName(context, "portal_catalog")

    portal_url = getToolByName(context, "portal_url")
    portal = portal_url.getPortalObject()
    path = "/".join(portal.getPhysicalPath())

    old_iface = "Products.CMFPlone.interfaces.syndication.ISiteSyndicationSettings"
    new_iface = "plone.base.interfaces.syndication.ISiteSyndicationSettings"

    fieldnames = [
        "allowed",
        "default_enabled",
        "search_rss_enabled",
        "show_author_info",
        "render_body",
        "max_items",
        "allowed_feed_types",
        "site_rss_items",
        "show_syndication_button",
        "show_syndication_link",
    ]

    # Make sure the interface is registered
    registry.registerInterface(ISiteSyndicationSettings)

    # write old record values to new record
    for fieldname in fieldnames:
        old_key = f"{old_iface}.{fieldname}"
        new_key = f"{new_iface}.{fieldname}"
        record = registry.records.get(old_key)
        if record is not None:
            if fieldname == "site_rss_items":
                # handle none existing items
                # if in path in catalog add to the record
                items = list(record.value) if record.value else ()
                newitems = []
                for item in items:
                    brains = portal_catalog(path={"query": f"{path}{item}", "depth": 0})
                    if len(brains) > 0:
                        brain = brains[0]
                        newitems.append(brain.UID)
                registry[new_key] = tuple(newitems)
            else:
                registry[new_key] = record.value

    # delete the old records
    for fieldname in fieldnames:
        key = f"{old_iface}.{fieldname}"
        if key in record_keys:
            del registry.records[key]


def _replace_values_in_record(record_name, *replacements):
    """Take the values of a registry record and replace some of them."""
    registry = getUtility(IRegistry)
    record = registry.records.get(record_name)
    if record is None:
        return
    values = record.value
    for _old, _new in replacements:
        if _old in values:
            values[values.index(_old)] = _new
    record.value = values


def fix_tinymce_format_iconnames(context):
    """Fix various TinyMCE formats to have the correct icon name.

    See https://github.com/plone/Products.CMFPlone/issues/3905
    """
    _replace_values_in_record(
        "plone.inline_styles",
        (
            "Strikethrough|strikethrough|strikethrough",
            "Strikethrough|strikethrough|strike-through",
        ),
        ("Code|code|code", "Code|code|sourcecode"),
    )
    _replace_values_in_record(
        "plone.alignment_styles",
        ("Left|alignleft|alignleft", "Left|alignleft|align-left"),
        ("Center|aligncenter|aligncenter", "Center|aligncenter|align-center"),
        ("Right|alignright|alignright", "Right|alignright|align-right"),
        ("Justify|alignjustify|alignjustify", "Justify|alignjustify|align-justify"),
    )
