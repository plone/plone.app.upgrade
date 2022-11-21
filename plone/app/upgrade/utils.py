from Acquisition import aq_base
from Missing import MV
from plone.base.utils import get_installer
from plone.indexer.interfaces import IIndexableObject
from Products.CMFCore.DirectoryView import _dirreg
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import base_hasattr
from Products.GenericSetup.interfaces import ISetupTool
from Products.GenericSetup.registry import _export_step_registry
from Products.GenericSetup.registry import _import_step_registry
from Products.PluginIndexes.util import safe_callable
from Products.ZCatalog.ProgressHandler import ZLogHandler
from types import ModuleType
from ZODB.POSException import ConflictError
from zope.component import ComponentLookupError
from zope.component import getMultiAdapter

import logging
import pkg_resources
import sys
import transaction


_marker = []

logger = logging.getLogger("plone.app.upgrade")

plone_version = pkg_resources.get_distribution("Products.CMFPlone").version


def version_match(target):
    """Given, our versioning scheme is always major.minorANYTHING, where major
    and minor are single-digit numbers, we can compare versions as follows.
    pkg_resources.parse_version is not compatible with our versioning scheme
    (like '5.0b1') and also not compatible with the semver.org proposal
    (requires '5.0-beta1').
    """
    # MAJOR.MINOR
    return (target[0], target[2]) == (plone_version[0], plone_version[2])


def null_upgrade_step(tool):
    """This is a null upgrade, use it when nothing happens"""
    pass


def safeEditProperty(obj, key, value, data_type="string"):
    """An add or edit function, surprisingly useful :)"""
    if obj.hasProperty(key):
        obj._updateProperty(key, value)
    else:
        obj._setProperty(key, value, data_type)


def addLinesToProperty(obj, key, values):
    if obj.hasProperty(key):
        data = getattr(obj, key)
        if isinstance(data, tuple):
            data = list(data)
        if isinstance(values, list):
            data.extend(values)
        else:
            data.append(values)
        obj._updateProperty(key, data)
    else:
        if not isinstance(values, list):
            values = [values]
        obj._setProperty(key, values, "lines")


def saveCloneActions(actionprovider):
    try:
        return True, actionprovider._cloneActions()
    except AttributeError:
        # Stumbled across ancient dictionary actions
        if not base_hasattr(actionprovider, "_convertActions"):
            return False, (
                "Can't convert actions of {}! Jumping to next "
                "action.".format(actionprovider.getId()),
                logging.ERROR,
            )
        else:
            actionprovider._convertActions()
            return True, actionprovider._cloneActions()


def testSkinLayer(skinsTool, layer):
    """Make sure a skin layer exists.

    layer can be a sub folder name, like captchas_core/dynamic
    or a/b/c/d/e.
    """
    # code adapted from CMFCore.SkinsContainer.getSkinByPath
    ob = aq_base(skinsTool)
    for name in layer.strip().split("/"):
        if not name:
            continue
        if name.startswith("_"):
            return 0
        ob = getattr(ob, name, None)
        if ob is None:
            return 0
    return 1


def cleanupSkinPath(portal, skinName, test=1):
    """Remove invalid skin layers from skins"""
    skinstool = getToolByName(portal, "portal_skins")
    selections = skinstool._getSelections()
    old_path = selections[skinName].split(",")
    new_path = []
    for layer in old_path:
        if layer and testSkinLayer(skinstool, layer):
            new_path.append(layer)
    skinstool.addSkinSelection(skinName, ",".join(new_path), test=test)


def cleanUpSkinsTool(context):
    """Cleanup the portal_skins tool.

    Initially this was created for Plone 4.0 alpha, but was factored out later.

    - Remove directory views for directories missing on the filesystem.

    - Remove invalid skin layers from all skin selections.
    """
    skins = getToolByName(context, "portal_skins")
    # Remove directory views for directories missing on the filesystem
    for name in skins.keys():
        directory_view = skins.get(name)
        reg_key = getattr(directory_view, "_dirpath", None)
        if not reg_key:
            # not a directory view, but a persistent folder
            continue
        try:
            # Removed in CMF 2.3
            if getattr(_dirreg, "getCurrentKeyFormat", None):
                reg_key = _dirreg.getCurrentKeyFormat(reg_key)
            _dirreg.getDirectoryInfo(reg_key)
        except ValueError:
            skins._delObject(name)

    transaction.savepoint(optimistic=True)
    existing = skins.keys()
    # Remove no longer existing entries from skin selections
    for layer, paths in skins.selections.items():
        new_paths = []
        for name in paths.split(","):
            if name in existing:
                new_paths.append(name)
            elif "/" in name and testSkinLayer(skins, name):
                new_paths.append(name)
            else:
                logger.info(
                    "Removed no longer existing path %s " "from skin selection %s.",
                    name,
                    layer,
                )
        skins.selections[layer] = ",".join(new_paths)


def cleanUpToolRegistry(context):
    portal = getToolByName(context, "portal_url").getPortalObject()
    toolset = context.getToolsetRegistry()
    required = toolset._required.copy()
    existing = portal.keys()
    changed = False
    items = list(required.items())
    for name, info in items:
        if name not in existing:
            del required[name]
            changed = True
    if changed:
        toolset._required = required
        logger.info("Cleaned up the toolset registry.")


def installOrReinstallProduct(portal, product_name, out=None, hidden=False):
    """Installs a product

    If product is already installed test if it needs to be reinstalled. Also
    fix skins after reinstalling
    """
    installer = get_installer(portal)
    if not installer.is_product_installed(product_name):
        installer.install_product(product_name, allow_hidden=True)
        logger.info("Installed %s", product_name)
    else:
        installer.upgrade_product(product_name)
        logger.info("Upgraded %s", product_name)
    # Refresh skins
    portal.clearCurrentSkin()
    if getattr(portal, "REQUEST", None):
        portal.setupCurrentSkin(portal.REQUEST)


def loadMigrationProfile(context, profile, steps=_marker):
    if not ISetupTool.providedBy(context):
        context = getToolByName(context, "portal_setup")
    if steps is _marker:
        context.runAllImportStepsFromProfile(profile, purge_old=False)
    else:
        for step in steps:
            context.runImportStepFromProfile(
                profile, step, run_dependencies=False, purge_old=False
            )


def alias_module(name, target):
    parts = name.split(".")
    i = 0
    module = None
    while i < len(parts) - 1:
        i += 1
        module_name = ".".join(parts[:i])
        try:
            __import__(module_name)
        except ImportError:
            new_module = ModuleType(module_name)
            sys.modules[module_name] = new_module
            if module is not None:
                setattr(module, parts[i - 1], new_module)
        module = sys.modules[module_name]

    setattr(module, parts[-1], target)
    # also make sure sys.modules is updated
    sys.modules[module_name + "." + parts[-1]] = target


def unregisterSteps(context, import_steps=None, export_steps=None):
    # This removes steps that are now registered via ZCML so are
    # duplicate.  Optionally, you can pass a list of extra
    # import_steps and/or export_steps to remove.
    if import_steps is None:
        import_steps = set()
    else:
        import_steps = set(import_steps)
    if export_steps is None:
        export_steps = set()
    else:
        export_steps = set(export_steps)
    registry = context.getImportStepRegistry()
    persistent_steps = registry.listSteps()
    zcml_steps = _import_step_registry.listSteps()
    duplicated = {s for s in persistent_steps if s in zcml_steps}
    remove = duplicated.union(import_steps)
    for step in remove:
        if step in registry._registered:
            registry.unregisterStep(step)
    registry = context.getExportStepRegistry()
    persistent_steps = registry.listSteps()
    zcml_steps = _export_step_registry.listSteps()
    duplicated = {s for s in persistent_steps if s in zcml_steps}
    remove = duplicated.union(export_steps)
    for step in remove:
        if step in registry._registered:
            registry.unregisterStep(step)
    context._p_changed = True


def _types_with_empty_icons(context, typesToUpdate):
    ttool = getToolByName(context, "portal_types")
    empty_icons = []
    for name in typesToUpdate.keys():
        fti = ttool.get(name)
        if fti:
            icon_expr = fti.getIconExprObject()
            if not icon_expr:
                empty_icons.append(name)
    return empty_icons


def _update_icon_in_single_brain(brain, typesToUpdate, getIconPos, metadata):
    # if the old icon is a standard icon, we assume no customization
    # has taken place and we can simply empty the getIcon metadata
    # without loading the object
    new_value = ""
    old_icons = typesToUpdate[brain.portal_type]
    brain_icon = brain.getIcon
    if brain_icon not in old_icons:
        # Otherwise we need to ask the object
        new_value = ""
        try:
            obj = brain.getObject()
        except KeyError:
            logger.warning("Ignoring brain without object: %s", brain.getURL())
            return
        method = getattr(aq_base(obj), "getIcon", None)
        if method is not None:
            try:
                new_value = obj.getIcon
                if callable(new_value):
                    new_value = new_value()
            except ConflictError:
                raise
            except Exception:
                new_value = ""
    if brain_icon != new_value:
        rid = brain.getRID()
        record = metadata[rid]
        new_record = list(record)
        new_record[getIconPos] = new_value
        metadata[rid] = tuple(new_record)


def updateIconsInBrains(context, typesToUpdate=None):
    """Update getIcon metadata column in given types.

    typesToUpdate must be a dictionary, for example: {
        # portal_type: ('old_icon.gif', 'new_icon.png'),
        'Document': ('document_icon.gif', 'document_icon.png'),
        }

    The portal_types must have an empty icon_expr, because that is the
    main use case.
    """
    if not typesToUpdate:
        logger.warn("No typesToUpdate given for updateIconsInBrains.")
        return

    catalog = getToolByName(context, "portal_catalog")
    logger.info("Updating `getIcon` metadata.")
    search = catalog.unrestrictedSearchResults
    _catalog = getattr(catalog, "_catalog", None)
    getIconPos = None
    if _catalog is not None:
        metadata = _catalog.data
        getIconPos = _catalog.schema.get("getIcon", None)
    empty_icons = _types_with_empty_icons(context, typesToUpdate)
    brains = search(portal_type=empty_icons, sort_on="path")
    num_objects = len(brains)
    pghandler = ZLogHandler(1000)
    pghandler.init("Updating getIcon metadata", num_objects)
    i = 0
    for brain in brains:
        pghandler.report(i)
        brain_icon = brain.getIcon
        if not brain_icon:
            continue
        if getIconPos is not None:
            _update_icon_in_single_brain(brain, typesToUpdate, getIconPos, metadata)
        else:
            # If we don't have a standard catalog tool, fall back to the
            # official API
            try:
                obj = brain.getObject()
            except KeyError:
                logger.warning("Ignoring brain without object: %s", brain.getURL())
                continue
            # passing in a valid but inexpensive index, makes sure we don't
            # reindex the entire catalog including expensive indexes like
            # SearchableText
            brain_path = brain.getPath()
            try:
                catalog.catalog_object(obj, brain_path, ["id"], True, pghandler)
            except ConflictError:
                raise
            except Exception:
                pass
        i += 1
    pghandler.finish()
    logger.info("Updated `getIcon` metadata.")


def update_catalog_metadata(context, column=None):
    """Update catalog metadata for all brains."""
    catalog = getToolByName(context, "portal_catalog")
    logger.info("Updating metadata.")
    # If we want to report progress, we need to know how many brains there are
    # and we can only do this if we have a list instead of a generator.
    brains = list(catalog.getAllBrains())
    num_objects = len(brains)
    pghandler = ZLogHandler(100)
    pghandler.init("Updating metadata", num_objects)

    column_position = metadata = None
    if column is not None:
        # We want to update one single column.
        # First check if it is there.
        if column not in catalog.schema():
            raise KeyError(
                "Column %s is not in the catalog schema: %s", column, catalog.schema()
            )
        # Updating a single column is only possible when relying on inner workings of
        # the catalog.  Find out if we have a regular ZCatalog and not something
        # special. Taken over from updateIconsInBrains above.
        _catalog = getattr(catalog, "_catalog", None)
        if _catalog is not None:
            metadata = _catalog.data
            column_position = _catalog.schema.get(column, None)

    for index, brain in enumerate(brains, 1):
        pghandler.report(index)
        try:
            obj = brain.getObject()
        except KeyError:
            logger.warning("Ignoring brain without object: %s", brain.getURL())
            continue
        if column_position is not None:
            # We rely on the inner workings of the catalog.
            rid = brain.getRID()
            record = metadata[rid]
            old_value = record[column_position]
            # see CMFPlone/catalog.zcml
            try:
                wrapper = getMultiAdapter((obj, catalog), IIndexableObject)
            except ComponentLookupError:
                # I have seen the portal_catalog as brain in the portal_catalog...
                logger.exception(obj)
                continue
            # See ZCatalog/Catalog.py:recordify
            new_value = getattr(wrapper, column, MV)
            if (new_value is not MV and safe_callable(new_value)):
                new_value = new_value()
            if old_value == new_value:
                continue
            new_record = list(record)
            new_record[column_position] = new_value
            metadata[rid] = tuple(new_record)
            continue
        # We can only update the metadata if we also update at least one index.
        # Passing in a valid but inexpensive index, makes sure we do not reindex the
        # entire catalog including expensive indexes like SearchableText.
        brain_path = brain.getPath()
        try:
            catalog.catalog_object(obj, brain_path, ["id"], True, pghandler)
        except ConflictError:
            raise
        except Exception:
            pass
    pghandler.finish()
    logger.info("Updated metadata of all brains.")


def get_property(context, property_name, default_value=None):
    try:
        return getattr(context, property_name, default_value)
    except AttributeError:
        return default_value
