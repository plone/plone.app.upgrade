from AccessControl.Permissions import view
from importlib.metadata import distribution
from importlib.metadata import PackageNotFoundError
from plone.app.upgrade.utils import loadMigrationProfile
from plone.base.interfaces import IMarkupSchema
from plone.base.interfaces import ISiteSchema
from plone.base.utils import base_hasattr
from plone.base.utils import get_installer
from plone.registry import field
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from zope.component import getUtility

import logging


logger = logging.getLogger("plone.app.upgrade")


try:
    distribution("plone.app.discussion")
    HAS_P_A_DISCUSSION = True
except PackageNotFoundError:
    HAS_P_A_DISCUSSION = False


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

    from plone.base.interfaces import ISiteSchema
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


def add_the_timezone_property(context):
    """Ensure that the portal_memberdata tool has the timezone property."""
    portal_memberdata = getToolByName(context, "portal_memberdata")
    if portal_memberdata.hasProperty("timezone"):
        return
    portal_memberdata.manage_addProperty("timezone", "", "string")


def add_get_application_json_to_weak_caching(context):
    """Add GET application/json for content to weak caching.

    See https://github.com/plone/plone.rest/issues/73#issuecomment-1384298492
    We want to get this in the templateRulesetMapping setting of the registry:

        <element key="GET_application_json_">plone.content.folderView</element>
    """
    registry = getUtility(IRegistry)
    try:
        from plone.app.caching.interfaces import IPloneCacheSettings
    except ImportError:
        # plone.app.caching is optional.
        return

    try:
        settings = registry.forInterface(IPloneCacheSettings)
    except KeyError:
        # It is available, but not activated.  Nothing to do.
        return
    mapping = settings.templateRulesetMapping
    key = "GET_application_json_"
    if key in mapping:
        # already set, do not change
        return
    mapping[key] = "plone.content.folderView"
    # Note: if we edit templateRulesetMapping, our change will not be persisted,
    # because it is a simple dict.  We have to set the entire mapping.
    settings.templateRulesetMapping = mapping
