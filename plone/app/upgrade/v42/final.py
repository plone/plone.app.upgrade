import logging
from plone.app.upgrade.utils import loadMigrationProfile
from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.upgrade import _upgrade_registry


logger = logging.getLogger('plone.app.upgrade')


def to42final_cmfeditions_registry_bases(context):
    """install the component registry bases modifier."""
    # for portals upgraded from older versions, the cmfeditions
    # profile isn't installed and so has no installed version number.
    # this applies a necessary upgrade step but also establishes a
    # version for the profile
    setup = getToolByName(context, 'portal_setup')

    # Copied from Products.GenericSetup.tool.SetupTool.manage_doUpgrades
    logger = logging.getLogger('GenericSetup')
    steps_to_run = ['36634937']
    profile_id = 'Products.CMFEditions:CMFEditions'
    step = None
    for step_id in steps_to_run:
        step = _upgrade_registry.getUpgradeStep(profile_id, step_id)
        if step is not None:
            step.doStep(setup)
            msg = "Ran upgrade step %s for profile %s" % (step.title,
                                                          profile_id)
            logger.log(logging.INFO, msg)

    # We update the profile version to the last one we have reached
    # with running an upgrade step.
    if step and step.dest is not None and step.checker is None:
        setup.setLastVersionForProfile(profile_id, step.dest)


def to42final(context):
    """4.2rc2 -> 4.2 final
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v42:to42final')


def to421(context):
    """4.2 -> 4.2.1
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v42:to421')
