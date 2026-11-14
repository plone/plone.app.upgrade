from Products.CMFCore.utils import getToolByName

import logging

logger = logging.getLogger(__name__)

CONTENTRULES_PROFILE = "plone.app.contentrules:default"
CONTENTRULES_BASELINE_VERSION = "7000"


def install_contentrules_profile(context):
    """Mark plone.app.contentrules as installed on existing sites.

    Up to Plone 6.2, Products.CMFPlone set up content rules itself.
    Since Plone 6.3 plone.app.contentrules has its own profile.  Existing
    sites already have storage, control panel, action and permissions, so
    we only add the browser layer and set the profile version.  We do not
    rerun the component registry step: that could replace an existing
    rule storage and lose rules.

    Existing sites match profile version 7000.  Stamping that baseline keeps
    later plone.app.contentrules upgrade steps pending instead of skipping them.
    """
    setup = getToolByName(context, "portal_setup")
    if not setup.profileExists(CONTENTRULES_PROFILE):
        logger.info("%s not available, skipping.", CONTENTRULES_PROFILE)
        return
    if setup.getLastVersionForProfile(CONTENTRULES_PROFILE) != "unknown":
        logger.info("%s already installed, skipping.", CONTENTRULES_PROFILE)
        return
    setup.runImportStepFromProfile(
        f"profile-{CONTENTRULES_PROFILE}", "browserlayer", run_dependencies=False
    )
    setup.setLastVersionForProfile(CONTENTRULES_PROFILE, CONTENTRULES_BASELINE_VERSION)
    logger.info("Registered %s as installed.", CONTENTRULES_PROFILE)
