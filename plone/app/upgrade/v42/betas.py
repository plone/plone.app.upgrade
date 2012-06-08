import logging

from AccessControl.Permission import Permission

from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.utils import installOrReinstallProduct
from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.upgrade import _upgrade_registry

logger = logging.getLogger('plone.app.upgrade')


def fixOwnerTuples(portal):
    # Repair owner tuples that contain the memberdata tool path.
    # Goes with the fix to PloneTool.changeOwnershipOf().
    def fixOwnerTuple(obj, path):
        old = obj.getOwnerTuple()
        if old and old[0][-1] == 'portal_memberdata':
            new = (['acl_users'], old[1])
            logger.info('Repairing %s: %r -> %r' % (path, old, new))
            obj._owner = new
    portal.ZopeFindAndApply(portal, search_sub=True, apply_func=fixOwnerTuple)


def installPloneAppDiscussion(portal):
    # Make sure plone.app.discussion is properly installed.
    installOrReinstallProduct(
        portal,
        "plone.app.discussion",
        out=None,
        hidden=True)


def to42beta1(context):
    """4.2a2 -> 4.2b1
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v42:to42beta1')


def to42beta1_owner_tuples(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    fixOwnerTuples(portal)


def to42beta2(context):
    """4.2b1 -> 4.2b2
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v42:to42beta2')


def to42rc1(context):
    """4.2b2 -> 4.2rc1
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v42:to42rc1')


def to42rc1_discussion(context):
    """Fix discussion
    """
    portal = getToolByName(context, 'portal_url').getPortalObject()
    installPloneAppDiscussion(portal)


def to42rc1_member_dashboard(context):
    """Add Member role to "Portlets: View dashboard" permission
    """

    p = 'Portlets: View dashboard'
    portal = getToolByName(context, 'portal_url').getPortalObject()
    roles = Permission(p, (), portal).getRoles(default=[])
    if not "Member" in roles:
        acquire = isinstance(roles, list) and True or False
        roles = list(roles)
        roles.append("Member")
        portal.manage_permission("Portlets: View dashboard",
                                 roles,
                                 acquire,
                                 )


def to42rc2(context):
    """4.2rc1 -> 4.2rc2
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v42:to42rc2')


def to42rc3_cmfeditions_registry_bases(context):
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
