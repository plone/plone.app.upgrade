from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.utils import update_catalog_metadata
from plone.base.utils import get_installer
from plone.dexterity.fti import DexterityFTI
from plone.registry.interfaces import IRegistry
from plone.uuid.interfaces import ATTRIBUTE_NAME
from plone.uuid.interfaces import IUUIDGenerator
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import IBundleRegistry
from time import time
from ZODB.broken import Broken
from zope.component import getUtility
from zope.component import queryUtility
from zope.component.hooks import getSite

import json
import logging
import os


logger = logging.getLogger("plone.app.upgrade")


def remove_temp_folder(context):
    """Remove temp_folder from Zope root if broken."""

    app = context.unrestrictedTraverse("/")
    broken_id = "temp_folder"
    if broken_id in app.objectIds():
        temp_folder = app.unrestrictedTraverse(broken_id, None)
        if not isinstance(temp_folder, Broken):
            logger.info("%s is not broken, so we keep it.", broken_id)
            return
        app._delObject(broken_id)
        logger.info("Removed broken %s from Zope root.", broken_id)

    # The root Zope object has a dictionary '_mount_points.
    # >>> app._mount_points
    # {'temp_folder': MountedObject(id='temp_folder')}
    if not hasattr(app, "_mount_points"):
        return
    if broken_id in app._mount_points:
        del app._mount_points[broken_id]
        app._p_changed = True
        logger.info("Removed %s from Zope root _mount_points.", broken_id)


FT_PROPERTIES_TO_KEEP = [
    "allow_discussion",
    "allowed_content_types",
    "default_view",
    "filter_content_types",
    "global_allow",
    "immediate_view",
    "view_methods",
]


def _migrate_blocks_of_root(portal):
    """Check if the portal was being used as a Volto site, and if so apply the relevant behavior"""

    if portal.hasProperty("blocks") and portal.hasProperty("blocks_layout"):
        # If the portal object has those properties it was being used
        # as a Volto site, so we need to set the volto.blocks behavior to the FTI
        # and copy the content of those properties to the fields
        pt = getToolByName(portal, "portal_types")
        fti = pt.getTypeInfo("Plone Site")
        fti.behaviors = fti.behaviors + ("volto.blocks",)

        blocks_property_value = portal.getProperty("blocks")
        blocks_layout_property_value = portal.getProperty("blocks_layout")
        portal.manage_delProperties(["blocks", "blocks_layout"])

        portal.blocks = json.loads(blocks_property_value)
        portal.blocks_layout = json.loads(blocks_layout_property_value)

        logger.info(
            "Applied volto.blocks behavior and migrated existing blocks of root properties."
        )


def change_plone_site_fti(context):
    pt = getToolByName(context, "portal_types")
    fti = pt.getTypeInfo("Plone Site")

    if isinstance(fti, DexterityFTI):
        # We assume the fti has been already fixed ...
        return

    # ... otherwise we fix it
    # keep important settings (often customized ones)
    keep = {prop: fti.getProperty(prop) for prop in FT_PROPERTIES_TO_KEEP}

    del pt["Plone Site"]

    loadMigrationProfile(context, "profile-plone.app.upgrade.v60:to_dx_site_root")

    # restore important settings
    fti = pt.getTypeInfo("Plone Site")
    for prop, value in keep.items():
        fti._setPropValue(prop, value)

    portal = getSite()
    _migrate_blocks_of_root(portal)


def make_site_dx(context):
    """Make the Plone Site a dexterity container"""
    portal = getSite()

    if portal._tree is not None:
        # We assume the object has been already initialized
        return

    portal._initBTrees()

    for obj_meta in portal._objects:
        obj_id = obj_meta["id"]
        logger.info("Migrating object %r", obj_id)
        # Load the content object ...
        obj = portal.__dict__.pop(obj_id)
        if not isinstance(obj, Broken) and obj_id not in (
            "portal_quickinstaller",
            "portal_form_controller",
        ):
            # ...and insert it into the btree.
            # Use _setOb so we don't reindex stuff: the paths stay the same.
            portal._setOb(obj_id, obj)

    delattr(portal, "_objects")
    portal._p_changed = True


def add_uuid_to_dxsiteroot(context):
    """Give the Plone Site an UUID."""
    portal = getSite()
    if getattr(portal, ATTRIBUTE_NAME, None):
        # we already have an UUID
        return
    generator = queryUtility(IUUIDGenerator)
    if generator is None:
        return
    uuid = generator()
    if not uuid:
        return
    setattr(portal, ATTRIBUTE_NAME, uuid)


def index_siteroot(context):
    """Index the Plone Site"""
    portal = getSite()
    portal.reindexObject()


def fix_unicode_properties(context):
    """Fix unicode properties.

    This does two things:

    1. Make sure lines contain only strings, instead of bytes,
       or worse: a combination of strings and bytes.
    2. Replace deprecated ulines, utext, utoken, and ustring properties
       with their non-unicode variant, using native strings.

    See https://github.com/plone/Products.CMFPlone/issues/3305

    The main function we use was added in Zope 5.4:
    https://github.com/zopefoundation/Zope/pull/993
    and improved in Zope 5.5:
    https://github.com/zopefoundation/Zope/pull/1009
    """
    from ZPublisher.utils import fix_properties

    portal = getSite()
    portal.ZopeFindAndApply(portal, search_sub=1, apply_func=fix_properties)


def cleanup_resources_and_bundles_in_registry(context=None):
    """Fix registry for es6 resources and new resource registry."""
    registry = getUtility(IRegistry)

    # We need to upgrade staticresources first.
    # Otherwise the bundles we delete will come back to haunt us
    context.upgradeProfile("plone.staticresources:default", dest="208")

    # Also reregister the newly defined plone.session bundle if it is installed.
    installer = get_installer(context)
    if installer.is_profile_installed("plone.session:default"):
        loadMigrationProfile(
            context, "profile-plone.session:default", steps=["plone.app.registry"]
        )

    # Remove obsolete records from the registry
    removed_keys = [
        "plone.resources/",
        "plone.lessvariables",
        "plone.resources.configjs",
        "plone.resources.last_legacy_import",
        "plone.resources.less-modify",
        "plone.resources.less-variables",
        "plone.resources.lessc",
        "plone.resources.requirejs",
        "plone.resources.rjs",
    ]
    to_delete = []
    for key in registry.records:
        for removed_key in removed_keys:
            if key.startswith(removed_key):
                to_delete.append(key)
                logger.debug(f"Removed record {key}")
                break
    for key in to_delete:
        del registry.records[key]
    logger.info(f"Removed {len(to_delete)} records from registry")

    # make sure they are all gone
    try:
        from Products.CMFPlone.interfaces import IResourceRegistry

        records = registry.collectionOfInterface(
            IResourceRegistry, prefix="plone.resources", check=False
        )
        assert len(records) == 0
    except ImportError:
        # the interface may be removed at some point
        pass

    # Remove obsolete bundles and reload the default bundles
    # The default bundles are reloaded in v60/profiles/to6003/registry.xml
    removed_bundles = [
        "filemanager",
        "plone-base",
        "plone-datatables",
        "plone-editor-tools",
        "plone-fontello",
        "plone-glyphicons",
        "plone-moment",
        "plone-tinymce",
        "resourceregistry",
        "thememapper",
        "plone-legacy",
        "plone-logged-in",
        "plone-session-pseudo-css",
        "plone-session-js",
    ]
    bundles = registry.collectionOfInterface(
        IBundleRegistry, prefix="plone.bundles", check=False
    )
    for name in removed_bundles:
        if name in bundles:
            del bundles[name]
            logger.info(f"Removed bundle {name}")

    # Remove deprecated bundle fields
    removed_fields = [
        "compile",
        "develop_css",
        "develop_javascript",
        "last_compilation",
        "merge_with",
        "resources",
        "stub_js_modules",
        "conditionalcomment",
    ]
    to_delete = []
    for key in registry.records:
        for removed_field in removed_fields:
            if key.startswith("plone.bundles/") and key.endswith(removed_field):
                to_delete.append(key)
                logger.debug(f"Removed record {key}")
    for key in to_delete:
        del registry.records[key]
    logger.info(f"Removed {len(to_delete)} deprecated bundle attributes from registry")

    # local default controlpanel icons
    loadMigrationProfile(
        context, "profile-Products.CMFPlone:plone", steps=["controlpanel"]
    )
    if installer.is_profile_installed("plone.app.theming:default"):
        loadMigrationProfile(
            context, "profile-plone.app.theming:default", steps=["controlpanel"]
        )
    if installer.is_profile_installed("plone.app.registry:default"):
        loadMigrationProfile(
            context, "profile-plone.app.registry:default", steps=["controlpanel"]
        )
    if installer.is_profile_installed("plone.app.caching:default"):
        loadMigrationProfile(
            context, "profile-plone.app.caching:default", steps=["controlpanel"]
        )
    if installer.is_profile_installed("Products.CMFPlacefulWorkflow:base"):
        loadMigrationProfile(
            context, "profile-Products.CMFPlacefulWorkflow:base", steps=["controlpanel"]
        )


def add_new_image_scales(context):
    """Add new image scales.

    See PLIP 3279, which adds and updates a few scales, and especially my
    comment on how we should handle upgrades:
    https://github.com/plone/Products.CMFPlone/issues/3279#issuecomment-1064970253

    Summary: we want an upgrade step in plone.app.upgrade that adds the
    completely new scales, without changing existing scales.
    """
    registry = getUtility(IRegistry)
    record = registry.records["plone.allowed_sizes"]
    new_scales = [
        "huge 1600:65536",
        "great 1200:65536",
        "larger 1000:65536",
        "teaser 600:65536",
    ]
    changed = False
    # Get the old/current value, without empty lines.
    old_value = [line for line in record.value if line.strip()]
    for line in new_scales:
        found = False
        new_name, new_dimensions = line.split()
        for old_line in old_value:
            try:
                old_name, old_dimensions = old_line.split()
            except (ValueError, KeyError, TypeError):
                continue
            if old_name == new_name:
                # A scale with this name is already defined.  Keep it.
                found = True
                break
        if found:
            continue
        old_value.append(line)
        logger.info("Added image scale: %s", line)
        changed = True

    if not changed:
        return

    def sorter(value):
        try:
            dimensions = value.strip().split()[-1]
            width, height = dimensions.split(":")
            width = int(width)
            height = int(height)
        except (ValueError, KeyError, TypeError):
            return (0, 0)
        return width, height

    # Sort the lines.
    new_value = sorted(old_value, key=sorter, reverse=True)

    # Explicitly save the record.
    record.value = new_value


def update_catalog_for_image_scales(context):
    """Update the catalog to add the image_scales column to all brains.

    This may take long.  By default we update, but we check an environment variable
    so you can switch this off:
    UPDATE_CATALOG_FOR_IMAGE_SCALES = 0
    """
    # We could catch TypeError and ValueError, but really this is a user error,
    # so let's fail.
    update = bool(int(os.getenv("UPDATE_CATALOG_FOR_IMAGE_SCALES", 1)))
    if not update:
        logger.warning(
            "UPDATE_CATALOG_FOR_IMAGE_SCALES is false, so not updating catalog."
        )
        return
    catalog = getToolByName(context, "portal_catalog")
    column = "image_scales"
    if column not in catalog.schema():
        catalog.addColumn(column)
        logger.info("Added %s column to catalog metadata schema.", column)
    start = time()
    update_catalog_metadata(context, column=column)
    end = time()
    minutes = (end - start) / 60
    logger.info("Time taken to update catalog for image scales: %.1f minutes.", minutes)


def upgrade_plone_module_profiles(context):
    """Upgrade profiles of core Plone modules to specific versions.

    This means: all packages that are installed when you use the Plone package.
    So this includes optional packages, like multilingual and plone.volto.
    We want to upgrade all of them to a specific version.

    Originally, when you upgrade a Plone 5.2 site to Plone 6.2, this happened:

    * We run all upgrade steps for Products.CMFPlone:plone to Plone 6.2.
    * Then we run all upgrade steps of the other modules.

    The danger is that an upgrade step that works now when Plone 6.0 alpha
    is the latest release, will not work when run on a 6.2 site.
    Or it may undo a plone.app.upgrade fix from 6.1.

    So the new idea is:

    * We run all upgrade steps for Products.CMFPlone:plone to Plone 6.0 alpha or
      beta, wherever we decide to put this function.
    * Then we call this function.  This runs all upgrade steps of the modules that
      were defined around that alpha/beta time.
    * Then we run the rest of the upgrade steps for Products.CMFPlone:plone to 6.2.
    * Then run any remaining upgrade steps for the other modules.

    See https://github.com/plone/Products.CMFPlone/issues/3346

    You can generate an up to date list if you first activate all modules,
    and then with `bin/instance debug` do this:

    >>> tool = app.Plone.portal_setup
    >>> for profile_id in tool.listProfilesWithUpgrades():
    ...     version = ".".join(tool.getLastVersionForProfile(profile_id))
    ...     print(f'("{profile_id}", "{version}"),')

    You must remove Products.CMFPlone:plone from the printed list:
    it would lead to recursion.

    Also, you may need to fix the plone.app.iterate version if it is unknown,
    due to a 'default' and 'plone.app.iterate' profile:

    >>> tool.getLastVersionForProfile('plone.app.iterate:default')

    See https://github.com/plone/plone.app.iterate/issues/99
    """
    profile_versions = (
        ("Products.CMFEditions:CMFEditions", "11"),
        ("Products.CMFPlacefulWorkflow:CMFPlacefulWorkflow", "1001"),
        # Do NOT add Products.CMFPlone:plone in here: it leads to recursion.
        ("Products.PlonePAS:PlonePAS", "5"),
        ("plone.app.caching:default", "3"),
        ("plone.app.contenttypes:default", "3000"),
        ("plone.app.dexterity:default", "2007"),
        ("plone.app.discussion:default", "2000"),
        ("plone.app.event:default", "15"),
        ("plone.app.iterate:plone.app.iterate", "121"),
        ("plone.app.multilingual:default", "1000"),
        ("plone.app.querystring:default", "14"),
        ("plone.app.theming:default", "1002"),
        ("plone.app.users:default", "1"),
        ("plone.restapi:default", "0006"),
        ("plone.session:default", "1003"),
        ("plone.staticresources:default", "213"),
        ("plone.volto:default", "1016"),
    )
    for profile_id, version in profile_versions:
        context.upgradeProfile(profile_id, dest=version, quiet=True)
