from BTrees.OOBTree import OOBTree
from plone.app.upgrade.utils import cleanUpSkinsTool
from plone.app.upgrade.utils import loadMigrationProfile
from plone.dexterity.interfaces import IDexterityFTI
from plone.folder.nogopip import manage_addGopipIndex
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.PlonePAS.tools.memberdata import MemberData
from zope.component import getUtility

import logging


logger = logging.getLogger("plone.app.upgrade")


def cleanup_resources():
    registry = getUtility(IRegistry)
    record = "plone.bundles/plone-legacy.resources"
    resources = registry.records[record]

    if "jquery-highlightsearchterms" in resources.value:
        resources.value.remove("jquery-highlightsearchterms")


def migrate_gopipindex(context):
    # GopipIndex class has moved from p.a.folder to p.folder
    # just remove and reinstall the index
    catalog = getToolByName(context, "portal_catalog")
    catalog.manage_delIndex("getObjPositionInParent")
    manage_addGopipIndex(catalog, "getObjPositionInParent")


def rebuild_memberdata(context):
    # MemberData has changed radically, see plone/Products.PlonePAS#24
    # This results in a bug in upgraded sites: plone/Products.CMFPlone#2722
    # We purge the _members storage of portal_memberdata and rebuild it
    # with new MemberData records that we get by creating them via a lookup of
    # all members in portal_membership.
    logger.info(
        "Rebuilding member data information. This step can take a while if "
        "your site has many users."
    )
    md_tool = getToolByName(context, "portal_memberdata")
    ms_tool = getToolByName(context, "portal_membership")
    # We cannot access data in _members any more, therefore purge it
    md_tool._members = OOBTree()
    # Iterate over all existing members and add their data to the tool again
    for member in ms_tool.searchForMembers():
        try:
            md = MemberData(member, md_tool)
            logger.info(f"Updated memberdata for {member}")
        # If we can't create a MemberData record for this member, skip it
        except Exception as e:
            logger.info(f"Skip broken memberdata for {member}: {e}")
            continue
        md_tool.registerMemberData(md._md, md.getId())


def fix_core_behaviors_in_ftis(context):
    # The behaviors for IRichText and ILeadImage have been renamed.
    # All FTIs that use them must be updated accordingly
    # See plone/plone.app.contenttypes#480
    types_tool = getToolByName(context, "portal_types")
    to_replace = {
        "plone.app.contenttypes.behaviors.richtext.IRichText": "plone.app.contenttypes.behaviors.richtext.IRichTextBehavior",
        "plone.app.contenttypes.behaviors.leadimage.ILeadImage": "plone.app.contenttypes.behaviors.leadimage.ILeadImageBehavior",
    }
    ftis = types_tool.listTypeInfo()
    for fti in ftis:
        # Since we're handling dexterity behaviors, we only care about
        # dexterity FTIs
        if not IDexterityFTI.providedBy(fti):
            continue
        behaviors = []
        change_needed = False
        for behavior in fti.behaviors:
            if behavior in to_replace:
                behavior = to_replace[behavior]
                change_needed = True
            behaviors.append(behavior)
        if change_needed:
            fti.behaviors = tuple(behaviors)


def to52alpha1(context):
    loadMigrationProfile(context, "profile-plone.app.upgrade.v52:to52alpha1")
    portal = getToolByName(context, "portal_url").getPortalObject()

    cleanUpSkinsTool(portal)

    cleanup_resources()
    migrate_gopipindex(context)
    rebuild_memberdata(context)
    fix_core_behaviors_in_ftis(context)
