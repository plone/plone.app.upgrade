from AccessControl.Permissions import view
from plone.app.upgrade.utils import loadMigrationProfile
from plone.base.utils import get_installer
from plone.registry import field
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IMarkupSchema
from Products.CMFPlone.interfaces import ISiteSchema
from Products.CMFPlone.utils import base_hasattr
from Products.CMFPlone.utils import safe_unicode
from zope.component import getUtility

import logging


logger = logging.getLogger("plone.app.upgrade")


def rebuild_redirections(context):
    """Rebuild the plone.app.redirector information.

    This initializes the date and manual information.
    """
    from plone.app.redirector.interfaces import IRedirectionStorage

    storage = getUtility(IRedirectionStorage)
    if not hasattr(storage, "_rebuild"):
        logger.warning(
            "Not rebuilding redirections: "
            "IRedirectionStorage misses the _rebuild method. "
        )
        return
    logger.info(
        "Starting rebuild of redirections to " "add date and manual information."
    )
    storage._rebuild()
    logger.info("Done rebuilding redirections.")


def move_dotted_to_named_behaviors(context):
    """named behaviors are better then dotted behaviors > let's move them."""
    from plone.behavior.registration import lookup_behavior_registration
    from plone.dexterity.interfaces import IDexterityFTI

    ptt = getToolByName(context, "portal_types")

    ftis = [fti for fti in ptt.objectValues() if IDexterityFTI.providedBy(fti)]

    for fti in ftis:
        behaviors = []
        for behavior in fti.behaviors:
            behavior_registration = lookup_behavior_registration(behavior)
            named_behavior = behavior_registration.name
            if named_behavior:
                behaviors.append(named_behavior)
                if named_behavior == behavior:
                    logger.info(
                        'Behavior "{behavior}" already named.'.format(
                            behavior=behavior,
                        ),
                    )
                else:
                    logger.info(
                        'Moved "{dotted}" to "{named}"'.format(
                            dotted=behavior,
                            named=named_behavior,
                        ),
                    )
            else:
                behaviors.append(behavior)
                logger.info(
                    '"{dotted}" has no name registered. '
                    "kept it dotted.".format(
                        dotted=behavior,
                    ),
                )
        fti.behaviors = tuple(behaviors)
        logger.info(
            "Converted dotted behaviors of {ct} to named behaviors.".format(
                ct=safe_unicode(fti.title),
            ),
        )

    logger.info("Done moving dotted to named behaviors.")
    # Make sure plone.staticresources is installed
    installer = get_installer(context)
    if not installer.is_product_installed("plone.staticresources"):
        installer.install_product("plone.staticresources")


KEYS_TO_CHANGE = [
    "plone.always_show_selector",
    "plone.authenticated_users_only",
    "plone.available_languages",
    "plone.default_language",
    "plone.display_flags",
    "plone.set_cookie_always",
    "plone.use_cctld_negotiation",
    "plone.use_combined_language_codes",
    "plone.use_content_negotiation",
    "plone.use_cookie_negotiation",
    "plone.use_path_negotiation",
    "plone.use_request_negotiation",
    "plone.use_subdomain_negotiation",
]
_marker = dict()
OLD_PREFIX = "Products.CMFPlone.interfaces.ILanguageSchema"
NEW_PREFIX = "plone.i18n.interfaces.ILanguageSchema"


def change_interface_on_lang_registry_records(context):
    """Interface Products.CMFPlone.interfaces.ILanguageSchema was moved to
    plone.i18n.interfaces."""
    registry = getUtility(IRegistry)
    for postfix in KEYS_TO_CHANGE:
        old_key = OLD_PREFIX + "." + postfix
        record = registry.records.get(old_key, _marker)
        if record is _marker:
            continue
        logger.info(f"Change registry key '{old_key}' to new interface.")
        record.field.interfaceName = NEW_PREFIX


def to521(context):
    """5.2.0 -> 5.2.1"""
    loadMigrationProfile(context, "profile-plone.app.upgrade.v52:to521")
    # Make sure plone.staticresources is installed
    installer = get_installer(context)
    if not installer.is_product_installed("plone.staticresources"):
        installer.install_product("plone.staticresources")


def to522(context):
    """5.2.1 -> 5.2.2"""
    loadMigrationProfile(context, "profile-plone.app.upgrade.v52:to522")


def move_markdown_transform_settings_to_registry(context):
    """Move markdown settings from portal_transforms to Plone registry."""
    registry = getUtility(IRegistry)
    try:
        settings = registry.forInterface(IMarkupSchema, prefix="plone")
    except KeyError:
        # Catch case where markdown_extensions is not yet registered
        registry.registerInterface(IMarkupSchema, prefix="plone")
        settings = registry.forInterface(IMarkupSchema, prefix="plone")
    pt = getToolByName(context, "portal_transforms")
    extensions = pt.markdown_to_html._config.get("enabled_extensions") or []
    extensions = [safe_unicode(ext) for ext in extensions]
    settings.markdown_extensions = extensions


def migrate_record_from_ascii_to_bytes(field_name, iface, prefix=None):
    """Migrate a configuration registry record from ASCII to Bytes.

    Note: this is intended as a utility method that third party code can use.

    Sample use:

    from Products.CMFPlone.interfaces import ISiteSchema
    migrate_record_from_ascii_to_bytes("plone.site_logo", ISiteSchema, prefix="plone")
    or:
    migrate_record_from_ascii_to_bytes("site_logo", ISiteSchema, prefix="plone")

    The interface is reregistered to get the new field definition.
    Note: this only works well if you have only *one* field that needs fixing.

    For the field name, using the full name including prefix is recommended.
    On Python 2 the full name is less needed, but on Python 3 it is.
    If you are not using a prefix when registering your interface,
    then automatically the identifier of your interface is used as prefix.
    In that case, you can use both of these:

    migrate_record_from_ascii_to_bytes("field_name", IMy)
    migrate_record_from_ascii_to_bytes(IMy.__identifier__ + ".field_name", IMy)
    """
    if prefix is None:
        prefix = iface.__identifier__
    if not prefix.endswith("."):
        prefix += "."
    if not field_name.startswith(prefix):
        field_name = prefix + field_name
    registry = getUtility(IRegistry)
    record = registry.records.get(field_name, None)
    if record is None:
        # Unexpected.  Registering the interface fixes this.
        registry.registerInterface(iface, prefix=prefix)
        return
    # Keep the original value so we can restore it.
    original_value = record.value
    if not isinstance(record.field, field.ASCII) and (
        original_value is None or isinstance(original_value, bytes)
    ):
        # All is well.
        # Actually, we might as well register the interface again for good measure.
        # For ISiteSchema I have seen a missing site_title field.
        registry.registerInterface(iface, prefix=prefix)
        return
    # Delete the bad record.
    # Calling registry.registerInterface would clean this up too,
    # but being explicit seems good here.
    del registry.records[field_name]
    # Make sure the interface is fully registered again.
    # This should recreate the field correctly.
    # Note: if you do this when the site logo is still an ASCII field,
    # the record will get replaced and the logo is gone!
    registry.registerInterface(iface, prefix=prefix)
    if original_value is None:
        # Nothing left to do.
        logger.info(
            "Replaced empty %s ASCII (native string) field with Bytes field.",
            field_name,
        )
        return
    new_record = registry.records[field_name]
    if isinstance(original_value, str):
        new_value = new_record.field.fromUnicode(original_value)
    elif isinstance(original_value, bytes):
        new_value = original_value
    else:
        # Seems impossible, but I like to be careful.
        return
    # Save the new value.
    new_record.value = new_value
    logger.info("Replaced %s ASCII (native string) field with Bytes field.", field_name)


def migrate_site_logo_from_ascii_to_bytes(context):
    """Site logo was ASCII field in 5.1, and Bytes field in 5.2.

    zope.schema.ASCII inherits from NativeString.
    With Python 2 this is the same as Bytes, but with Python 3 not:
    you get a WrongType error when saving the site-controlpanel.
    """
    migrate_record_from_ascii_to_bytes("plone.site_logo", ISiteSchema, prefix="plone")


def _recursive_strict_permission(obj):
    obj.manage_permission(view, ("Manager", "Owner"), 0)
    if base_hasattr(obj, "objectValues"):
        for child in obj.objectValues():
            _recursive_strict_permission(child)


def secure_portal_setup_objects(context):
    """Make portal_setup objects accessible only to Manager/Owner.

    This matches the GenericSetup code for new logs and snapshots.
    See https://github.com/zopefoundation/Products.GenericSetup/pull/102
    """
    # context conveniently is the portal_setup too.
    # Set permission on the sub objects of the setup tool, which are the logs.
    for child in context.objectValues():
        # Recursive is not strictly needed, but it does not hurt.
        _recursive_strict_permission(child)
    logger.info("Made portal_setup logs only available for Manager and Owner.")

    # And now the snapshot folder and sub items, if they exist.
    if not base_hasattr(context, "snapshots"):
        return
    _recursive_strict_permission(context.snapshots)
    logger.info("Made portal_setup snapshots only available for Manager and Owner.")
