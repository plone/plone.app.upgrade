# -*- coding: utf-8 -*-
from plone.app.upgrade.utils import loadMigrationProfile
from plone.dexterity.fti import DexterityFTI
from plone.uuid.interfaces import ATTRIBUTE_NAME
from plone.uuid.interfaces import IUUIDGenerator
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import safe_unicode
from ZODB.broken import Broken
from zope.component import queryUtility
from zope.component.hooks import getSite

import logging


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


def _string_tuple(value):
    # Copy of ZPublisher.utils._string_tuple which will be released in Zope 5.4.
    if not value:
        return ()
    return tuple([safe_unicode(element) for element in value])


def _fix_properties(obj, path=None):
    """Fix properties on object.

    Copy of ZPublisher.utils.fix_properties which will be released in Zope 5.4.
    See https://github.com/zopefoundation/Zope/pull/993

    This does two things:

    1. Make sure lines contain only strings, instead of bytes,
       or worse: a combination of strings and bytes.
    2. Replace deprecated ulines, utext, utoken, and ustring properties
       with their non-unicode variant, using native strings.

    See https://github.com/zopefoundation/Zope/issues/987

    Since Zope 5.3, a lines property stores strings instead of bytes.
    But there is no migration yet.  (We do that here.)
    Result is that getProperty on an already created lines property
    will return the old value with bytes, but a newly created lines property
    will return strings.  And you might get combinations.

    Also since Zope 5.3, the ulines property type is deprecated.
    You should use a lines property instead.
    Same for a few others: utext, utoken, ustring.
    The unicode variants are planned to be removed in Zope 6.

    Intended usage:
    app.ZopeFindAndApply(app, search_sub=1, apply_func=fix_properties)
    """
    if path is None:
        # When using ZopeFindAndApply, path is always given.
        # But we may be called by other code.
        if hasattr(object, 'getPhysicalPath'):
            path = '/'.join(object.getPhysicalPath())
        else:
            # Some simple object, for example in tests.
            # We don't care about the path then, it is only shown in logs.
            path = "/dummy"

    try:
        prop_map = obj.propertyMap()
    except AttributeError:
        # Object does not inherit from PropertyManager.
        # For example 'MountedObject'.
        return

    for prop_info in prop_map:
        # Example: {'id': 'title', 'type': 'string', 'mode': 'w'}
        prop_id = prop_info.get("id")
        current = obj.getProperty(prop_id)
        if current is None:
            continue
        new_type = prop_type = prop_info.get("type")
        if prop_type == "lines":
            new = _string_tuple(current)
        elif prop_type == "ulines":
            new_type = "lines"
            new = _string_tuple(current)
        elif prop_type == "utokens":
            new_type = "tokens"
            new = _string_tuple(current)
        elif prop_type == "utext":
            new_type = "text"
            new = safe_unicode(current)
        elif prop_type == "ustring":
            new_type = "string"
            new = safe_unicode(current)
        else:
            continue
        if prop_type != new_type:
            # Replace with non-unicode variant.
            # This could easily lead to:
            # Exceptions.BadRequest: Invalid or duplicate property id.
            #   obj._delProperty(prop_id)
            #   obj._setProperty(prop_id, new, new_type)
            # So fix it by using internal details.
            for prop in obj._properties:
                if prop.get("id") == prop_id:
                    prop["type"] = new_type
                    obj._p_changed = True
                    break
            else:
                # This probably cannot happen.
                # If it does, we want to know.
                logger.warning(
                    "Could not change property %s from %s to %s for %s",
                    prop_id,
                    prop_type,
                    new_type,
                    path,
                )
                continue
            obj._updateProperty(prop_id, new)
            logger.info(
                "Changed property %s from %s to %s for %s",
                prop_id,
                prop_type,
                new_type,
                path,
            )
            continue
        if current != new:
            obj._updateProperty(prop_id, new)
            logger.info(
                "Changed property %s at %s so value fits the type %s: %r",
                prop_id,
                path,
                prop_type,
                new,
            )


def fix_unicode_properties(context):
    """Fix unicode properties.

    This does two things:

    1. Make sure lines contain only strings, instead of bytes,
       or worse: a combination of strings and bytes.
    2. Replace deprecated ulines, utext, utoken, and ustring properties
       with their non-unicode variant, using native strings.

    See https://github.com/plone/Products.CMFPlone/issues/3305

    The main function we use here will be in Zope 5.4:
    https://github.com/zopefoundation/Zope/pull/993
    If it is not there, we use our own copy.
    The Zope one should be leading though.
    Our copy can be removed when Zope 5.4. is released.
    """
    try:
        from ZPublisher.utils import fix_properties
    except ImportError:
        fix_properties = _fix_properties
    portal = getSite()
    portal.reindexObject()
    portal.ZopeFindAndApply(portal, search_sub=1, apply_func=fix_properties)
