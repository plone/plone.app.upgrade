# -*- coding: utf-8 -*-
from Acquisition import aq_base
from Products.CMFCore.DirectoryView import _dirreg
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import base_hasattr
from Products.GenericSetup.interfaces import ISetupTool
from Products.GenericSetup.registry import _export_step_registry
from Products.GenericSetup.registry import _import_step_registry
from Products.ZCatalog.ProgressHandler import ZLogHandler
from types import ModuleType
from ZODB.POSException import ConflictError

import logging
import pkg_resources
import sys
import transaction


_marker = []

logger = logging.getLogger('plone.app.upgrade')

plone_version = pkg_resources.get_distribution('Products.CMFPlone').version


def version_match(target):
    """ Given, our versioning scheme is always major.minorANYTHING, where major
    and minor are single-digit numbers, we can compare versions as follows.
    pkg_resources.parse_version is not compatible with our versioning scheme
    (like '5.0b1') and also not compatible with the semver.org proposal
    (requires '5.0-beta1').
    """
    # MAJOR.MINOR
    return (target[0], target[2]) == (plone_version[0], plone_version[2])


def null_upgrade_step(tool):
    """ This is a null upgrade, use it when nothing happens """
    pass


def safeEditProperty(obj, key, value, data_type='string'):
    """ An add or edit function, surprisingly useful :) """
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
        obj._setProperty(key, values, 'lines')


def saveCloneActions(actionprovider):
    try:
        return True, actionprovider._cloneActions()
    except AttributeError:
        # Stumbled across ancient dictionary actions
        if not base_hasattr(actionprovider, '_convertActions'):
            return False, (
                "Can't convert actions of {0}! Jumping to next "
                'action.'.format(actionprovider.getId()), logging.ERROR)
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
    for name in layer.strip().split('/'):
        if not name:
            continue
        if name.startswith('_'):
            return 0
        ob = getattr(ob, name, None)
        if ob is None:
            return 0
    return 1


def cleanupSkinPath(portal, skinName, test=1):
    """Remove invalid skin layers from skins"""
    skinstool = getToolByName(portal, 'portal_skins')
    selections = skinstool._getSelections()
    old_path = selections[skinName].split(',')
    new_path = []
    for layer in old_path:
        if layer and testSkinLayer(skinstool, layer):
            new_path.append(layer)
    skinstool.addSkinSelection(skinName, ','.join(new_path), test=test)


def cleanUpSkinsTool(context):
    """Cleanup the portal_skins tool.

    Initially this was created for Plone 4.0 alpha, but was factored out later.

    - Remove directory views for directories missing on the filesystem.

    - Remove invalid skin layers from all skin selections.
    """
    skins = getToolByName(context, 'portal_skins')
    # Remove directory views for directories missing on the filesystem
    for name in skins.keys():
        directory_view = skins.get(name)
        reg_key = getattr(directory_view, '_dirpath', None)
        if not reg_key:
            # not a directory view, but a persistent folder
            continue
        try:
            # Removed in CMF 2.3
            if getattr(_dirreg, 'getCurrentKeyFormat', None):
                reg_key = _dirreg.getCurrentKeyFormat(reg_key)
            _dirreg.getDirectoryInfo(reg_key)
        except ValueError:
            skins._delObject(name)

    transaction.savepoint(optimistic=True)
    existing = skins.keys()
    # Remove no longer existing entries from skin selections
    for layer, paths in skins.selections.items():
        new_paths = []
        for name in paths.split(','):
            if name in existing:
                new_paths.append(name)
            elif '/' in name and testSkinLayer(skins, name):
                new_paths.append(name)
            else:
                logger.info('Removed no longer existing path %s '
                            'from skin selection %s.', name, layer)
        skins.selections[layer] = ','.join(new_paths)


def installOrReinstallProduct(portal, product_name, out=None, hidden=False):
    """Installs a product

    If product is already installed test if it needs to be reinstalled. Also
    fix skins after reinstalling
    """
    try:
        from Products.CMFPlone.utils import get_installer
    except ImportError:
        # BBB For Plone 5.0 and lower.
        qi = getToolByName(portal, 'portal_quickinstaller', None)
        if qi is None:
            return
        old_qi = True
    else:
        qi = get_installer(portal)
        old_qi = False
    if old_qi:
        if not qi.isProductInstalled(product_name):
            qi.installProduct(product_name, hidden=hidden)
            logger.info('Installed %s', product_name)
        elif old_qi:
            info = qi._getOb(product_name)
            installed_version = info.getInstalledVersion()
            product_version = qi.getProductVersion(product_name)
            if installed_version != product_version:
                qi.reinstallProducts([product_name])
                logger.info(
                    '%s is out of date (installed: %s/ filesystem: %s), '
                    'reinstalled.',
                    product_name, installed_version, product_version)
            else:
                logger.info('%s already installed.', product_name)
    else:
        # New QI browser view.
        if not qi.is_product_installed(product_name):
            qi.install_product(product_name, allow_hidden=True)
            logger.info('Installed %s', product_name)
        else:
            qi.upgrade_product(product_name)
            logger.info('Upgraded %s', product_name)
    # Refresh skins
    portal.clearCurrentSkin()
    if getattr(portal, 'REQUEST', None):
        portal.setupCurrentSkin(portal.REQUEST)


def loadMigrationProfile(context, profile, steps=_marker):
    if not ISetupTool.providedBy(context):
        context = getToolByName(context, 'portal_setup')
    if steps is _marker:
        context.runAllImportStepsFromProfile(profile, purge_old=False)
    else:
        for step in steps:
            context.runImportStepFromProfile(profile,
                                             step,
                                             run_dependencies=False,
                                             purge_old=False)


def alias_module(name, target):
    parts = name.split('.')
    i = 0
    module = None
    while i < len(parts) - 1:
        i += 1
        module_name = '.'.join(parts[:i])
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
    sys.modules[module_name + '.' + parts[-1]] = target


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
    duplicated = set([s for s in persistent_steps if s in zcml_steps])
    remove = duplicated.union(import_steps)
    for step in remove:
        if step in registry._registered:
            registry.unregisterStep(step)
    registry = context.getExportStepRegistry()
    persistent_steps = registry.listSteps()
    zcml_steps = _export_step_registry.listSteps()
    duplicated = set([s for s in persistent_steps if s in zcml_steps])
    remove = duplicated.union(export_steps)
    for step in remove:
        if step in registry._registered:
            registry.unregisterStep(step)
    context._p_changed = True


def _types_with_empty_icons(context, typesToUpdate):
    ttool = getToolByName(context, 'portal_types')
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
    new_value = ''
    old_icons = typesToUpdate[brain.portal_type]
    brain_icon = brain.getIcon
    if brain_icon not in old_icons:
        # Otherwise we need to ask the object
        new_value = ''
        obj = brain.getObject()
        method = getattr(aq_base(obj), 'getIcon', None)
        if method is not None:
            try:
                new_value = obj.getIcon
                if callable(new_value):
                    new_value = new_value()
            except ConflictError:
                raise
            except Exception:
                new_value = ''
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
        logger.warn('No typesToUpdate given for updateIconsInBrains.')
        return

    catalog = getToolByName(context, 'portal_catalog')
    logger.info('Updating `getIcon` metadata.')
    search = catalog.unrestrictedSearchResults
    _catalog = getattr(catalog, '_catalog', None)
    getIconPos = None
    if _catalog is not None:
        metadata = _catalog.data
        getIconPos = _catalog.schema.get('getIcon', None)
    empty_icons = _types_with_empty_icons(context, typesToUpdate)
    brains = search(portal_type=empty_icons, sort_on='path')
    num_objects = len(brains)
    pghandler = ZLogHandler(1000)
    pghandler.init('Updating getIcon metadata', num_objects)
    i = 0
    for brain in brains:
        pghandler.report(i)
        brain_icon = brain.getIcon
        if not brain_icon:
            continue
        if getIconPos is not None:
            _update_icon_in_single_brain(
                brain, typesToUpdate, getIconPos, metadata)
        else:
            # If we don't have a standard catalog tool, fall back to the
            # official API
            obj = brain.getObject()
            # passing in a valid but inexpensive index, makes sure we don't
            # reindex the entire catalog including expensive indexes like
            # SearchableText
            brain_path = brain.getPath()
            try:
                catalog.catalog_object(
                    obj, brain_path, ['id'], True, pghandler)
            except ConflictError:
                raise
            except Exception:
                pass
        i += 1
    pghandler.finish()
    logger.info('Updated `getIcon` metadata.')


def get_property(context, property_name, default_value=None):
    try:
        return getattr(context, property_name, default_value)
    except AttributeError:
        return default_value
