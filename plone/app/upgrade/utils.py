import logging
import new
import sys
from types import ListType, TupleType

from Acquisition import aq_base
from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.interfaces import ISetupTool
from Products.GenericSetup.registry import _export_step_registry
from Products.GenericSetup.registry import _import_step_registry
from Products.ZCatalog.ProgressHandler import ZLogHandler
from ZODB.POSException import ConflictError

import pkg_resources

_marker = []

logger = logging.getLogger('plone.app.upgrade')

plone_version = pkg_resources.get_distribution("Products.CMFPlone").version


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
        if type(data) is TupleType:
            data = list(data)
        if type(values) is ListType:
            data.extend(values)
        else:
            data.append(values)
        obj._updateProperty(key, data)
    else:
        if type(values) is not ListType:
            values = [values]
        obj._setProperty(key, values, 'lines')


def saveCloneActions(actionprovider):
    try:
        return True, actionprovider._cloneActions()
    except AttributeError:
        # Stumbled across ancient dictionary actions
        if not hasattr(aq_base(actionprovider), '_convertActions'):
            return False, ("Can't convert actions of %s! Jumping to next "
                           "action." % actionprovider.getId(), logging.ERROR)
        else:
            actionprovider._convertActions()
            return True, actionprovider._cloneActions()


def testSkinLayer(skinsTool, layer):
    """Make sure a skin layer exists"""
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


def installOrReinstallProduct(portal, product_name, out=None, hidden=False):
    """Installs a product

    If product is already installed test if it needs to be reinstalled. Also
    fix skins after reinstalling
    """
    qi = getToolByName(portal, 'portal_quickinstaller')
    if not qi.isProductInstalled(product_name):
        qi.installProduct(product_name, hidden=hidden)
        # Refresh skins
        portal.clearCurrentSkin()
        if getattr(portal, 'REQUEST', None):
            portal.setupCurrentSkin(portal.REQUEST)
        logger.info("Installed %s" % product_name)
    else:
        info = qi._getOb(product_name)
        installed_version = info.getInstalledVersion()
        product_version = qi.getProductVersion(product_name)
        if installed_version != product_version:
            qi.reinstallProducts([product_name])
            logger.info("%s is out of date (installed: %s/ filesystem: %s), "
                        "reinstalled." % (product_name, installed_version,
                                          product_version))
        else:
            logger.info('%s already installed.' % product_name)


def loadMigrationProfile(context, profile, steps=_marker):
    if not ISetupTool.providedBy(context):
        context = getToolByName(context, "portal_setup")
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
            new_module = new.module(module_name)
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
    ttool = getToolByName(context, 'portal_types')
    empty_icons = []
    for name in typesToUpdate.keys():
        fti = ttool.get(name)
        if fti:
            icon_expr = fti.getIconExprObject()
            if not icon_expr:
                empty_icons.append(name)

    brains = search(portal_type=empty_icons, sort_on="path")
    num_objects = len(brains)
    pghandler = ZLogHandler(1000)
    pghandler.init('Updating getIcon metadata', num_objects)
    i = 0
    for brain in brains:
        pghandler.report(i)
        brain_icon = brain.getIcon
        if not brain_icon:
            continue
        old_icons = typesToUpdate[brain.portal_type]
        if getIconPos is not None:
            # if the old icon is a standard icon, we assume no customization
            # has taken place and we can simply empty the getIcon metadata
            # without loading the object
            new_value = ''
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
        else:
            # If we don't have a standard catalog tool, fall back to the
            # official API
            obj = brain.getObject()
            # passing in a valid but inexpensive index, makes sure we don't
            # reindex the entire catalog including expensive indexes like
            # SearchableText
            brain_path = brain.getPath()
            try:
                catalog.catalog_object(obj, brain_path, ['id'], True, pghandler)
            except ConflictError:
                raise
            except Exception:
                pass
        i += 1
    pghandler.finish()
    logger.info('Updated `getIcon` metadata.')
