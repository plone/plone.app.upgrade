from plone.app.upgrade.utils import cleanUpToolRegistry
from plone.app.upgrade.utils import loadMigrationProfile
from plone.base.utils import get_installer
from Products.CMFCore.utils import getToolByName
from types import ModuleType
from zc.relation.interfaces import ICatalog
from zope import component
from zope.interface import Interface
from zope.intid.interfaces import IIntIds
from zope.intid.interfaces import IntIdMissingError
from zope.intid.interfaces import ObjectMissingError

import logging
import sys


logger = logging.getLogger("plone.app.upgrade")


def add_exclude_from_nav_index(context):
    """Add exclude_from_nav index to the portal_catalog."""
    name = "exclude_from_nav"
    meta_type = "BooleanIndex"
    catalog = getToolByName(context, "portal_catalog")
    indexes = catalog.indexes()
    indexables = []
    if name not in indexes:
        catalog.addIndex(name, meta_type)
        indexables.append(name)
        logger.info("Added %s for field %s.", meta_type, name)
    if len(indexables) > 0:
        logger.info("Indexing new indexes %s.", ", ".join(indexables))
        catalog.manage_reindexIndex(ids=indexables)


def remove_legacy_resource_registries(context):
    """Remove portal_css and portal_javascripts."""
    portal_url = getToolByName(context, "portal_url")
    portal = portal_url.getPortalObject()

    tools_to_remove = [
        "portal_css",
        "portal_javascripts",
    ]

    # remove obsolete tools
    for tool in tools_to_remove:
        if tool not in portal:
            continue
        portal._delObject(tool)

    cleanUpToolRegistry(context)


def remove_interface_indexes_from_relations_catalog():
    """remove unused interface indexes from relations catalog"""
    logger.info("Removing unused interface indexes from relations catalog.")
    catalog = component.queryUtility(ICatalog)
    indexes_to_remove = ["from_interfaces_flattened", "to_interfaces_flattened"]
    for index_to_remove in indexes_to_remove:
        if index_to_remove in catalog._name_TO_mapping:
            catalog.removeValueIndex(index_to_remove)

    # Avoid "RuntimeError: the bucket being iterated changed size" by first
    # getting all tokens. This might need lots of RAM on large databases
    tokens = [token for token in catalog._relTokens]
    empty = 0
    for token in tokens:
        try:
            relation = catalog.resolveRelationToken(token)
        except ObjectMissingError:
            logger.warning("Removed token with missing object.")
            catalog._relTokens.remove(token)
            continue

        if relation.from_object is not None or relation.to_object is not None:
            continue
        catalog.unindex_doc(token)
        empty += 1
    if empty:
        logger.warning("Removed %s empty relations.", empty)

    # Get rid of broken relations, where intid no longer exists.
    # Those broken need to be removed for a later zodbupdate.
    relations = [rel for rel in catalog]
    intids = component.getUtility(IIntIds)
    added_rel_intids = 0
    for rel in relations:
        try:
            intids.getId(rel)
        except KeyError:
            intids.register(rel)
            added_rel_intids += 1
        try:
            catalog.unindex(rel)
        except KeyError:
            logger.warning("Broken relation ignored due to impossible unindex")
            # there are rare cases with broken relations where the attributes
            # are not complete, those can be ignored
            continue
        try:
            catalog.index(rel)
        except IntIdMissingError:
            logger.warning("Broken relation removed.")
    if added_rel_intids:
        logger.info(
            "Registered %s extra relations in the intid utility.", added_rel_intids
        )


class IResourceRegistriesSettings(Interface):
    """fake/mock interface to be able to remove non existing dotted path"""

    pass


FAKE_RR_PATH = (
    "Products.ResourceRegistries.interfaces.settings." "IResourceRegistriesSettings"
)


def to52beta1(context):
    # fake the old ResourceRegistries interface:
    fake_mods = FAKE_RR_PATH.split(".")[:-1]
    parent = sys.modules[fake_mods[0]]
    for idx in range(1, len(fake_mods)):
        mod_name = ".".join(fake_mods[: idx + 1])
        mod_inst = ModuleType(mod_name)
        if parent:
            setattr(parent, fake_mods[idx], mod_inst)
        sys.modules[mod_name] = parent = mod_inst
    sys.modules[FAKE_RR_PATH] = IResourceRegistriesSettings
    setattr(parent, "IResourceRegistriesSettings", IResourceRegistriesSettings)
    sys.modules[FAKE_RR_PATH]
    loadMigrationProfile(context, "profile-plone.app.upgrade.v52:to52beta1")
    for idx in range(1, len(fake_mods)):
        mod_name = ".".join(fake_mods[: idx + 1])
        del sys.modules[mod_name]
    del sys.modules[FAKE_RR_PATH]
    delattr(sys.modules[fake_mods[0]], fake_mods[1])
    add_exclude_from_nav_index(context)
    remove_legacy_resource_registries(context)
    remove_interface_indexes_from_relations_catalog()
    # Make sure plone.staticresources is installed
    installer = get_installer(context)
    if not installer.is_product_installed("plone.staticresources"):
        installer.install_product("plone.staticresources")


def to52rc1(context):
    loadMigrationProfile(context, "profile-plone.app.upgrade.v52:to52rc1")
    # Make sure plone.staticresources is installed
    installer = get_installer(context)
    if not installer.is_product_installed("plone.staticresources"):
        installer.install_product("plone.staticresources")
