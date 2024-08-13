from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from Acquisition import aq_parent
from importlib.metadata import distribution
from importlib.metadata import PackageNotFoundError
from plone.app.upgrade.utils import loadMigrationProfile
from plone.browserlayer.utils import unregister_layer
from Products.CMFCore.utils import getToolByName
from zope.component import getSiteManager

import logging


logger = logging.getLogger(__name__)


def remove_portal_properties_tool(context):
    """Remove the portal_properties tool.

    Core Plone has moved to the configuration registry in Plone 5.0.
    Add-ons may have still used it, but we announced we would remove
    it in Plone 6.1.
    """
    portal = getToolByName(context, "portal_url").getPortalObject()
    tool = getattr(portal, "portal_properties", None)
    if tool is None:
        return
    # portal._delObject("portal_properties") would give:
    # AttributeError: 'PropertiesTool' object has no attribute '__of__'
    portal._delOb("portal_properties")
    logger.info("Removed portal_properties tool.")


def maybe_cleanup_discussion(context):
    """Cleanup some left-overs from plone.app.discussion.

    But only do this when the package is not available.
    In Plone 6.1, the package was made into a core add-on.
    Meaning: it no longer gets pulled in by Products.CMFPlone,
    but only by the Plone package.
    """
    # First check if the GS profile was installed.
    profile_id = "plone.app.discussion:default"
    if context.getLastVersionForProfile(profile_id) == "unknown":
        logger.info("%s was not installed, nothing to do.", profile_id)
        return
    try:
        distribution("plone.app.discussion")
        logger.info("The plone.app.discussion package is available, so we do nothing.")
        return
    except PackageNotFoundError:
        logger.info("plone.app.discussion package not found, will cleanup.")

    # First check if there are any actual discussion items in the site.
    catalog = getToolByName(context, "portal_catalog")
    brains = catalog.unrestrictedSearchResults(portal_type="Discussion Item")
    total = len(brains)
    if total:
        raise ValueError(
            f"{total} Discussion Items (comments) were found in the site, but "
            "plone.app.discussion is missing.\nThis package is optional since "
            "Plone 6.1.\nPlease add plone.app.discussion to your Plone installation "
            "if you want to keep using them."
        )

    # First apply a profile.  This is mostly a copy of the uninstall profile
    # of plone.app.discussion.
    loadMigrationProfile(context, "profile-plone.app.upgrade.v61:uninstall-discussion")

    # The registry keys were registered via the IDiscussionSettings interface
    # which no longer exists, so we remove them one by one.
    registry = getUtility(IRegistry)
    records = registry.records
    to_remove = [
        key
        for key in records.keys()
        if "plone.app.discussion.interfaces.IDiscussionSettings" in key
    ]
    for key in to_remove:
        del records[key]
    logger.info("Removed all IDiscussionSettings registry records.")

    # Gather the FTIs that have the plone.allowdiscussion behavior.
    # It can appear with the name or the interface identifier.
    portal_types = getToolByName(context, "portal_types")
    old_behaviors = {
        "plone.allowdiscussion",
        "plone.app.dexterity.behaviors.discussion.IAllowDiscussion",
    }
    ftis_to_fix = (
        fti
        for fti in portal_types.objectValues("Dexterity FTI")
        if set(fti.behaviors) & old_behaviors
    )
    for fti in ftis_to_fix:
        # Remove the behavior.  Remember this is a tuple.
        behaviors = [
            behavior for behavior in fti.behaviors if behavior not in old_behaviors
        ]
        # Set the updated behaviors
        fti.behaviors = tuple(behaviors)
        logger.info("Removed plone.allowdiscussion behavior from %s", fti)

    # Mark GS profile as not installed/activated.
    context.unsetLastVersionForProfile(profile_id)
