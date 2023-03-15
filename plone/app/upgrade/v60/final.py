from AccessControl.Permission import Permission
from zope.component.hooks import getSite

import logging


logger = logging.getLogger(__name__)
SITE_ADMIN = "Site Administrator"
SITE_ADMIN_PERMISSIONS = [
    "Inspect Relations",
    "Plone Site Setup: Editing",
    "Plone Site Setup: Filtering",
    "Plone Site Setup: Language",
    "Plone Site Setup: Mail",
    "Plone Site Setup: Markup",
    "Plone Site Setup: Navigation",
    "Plone Site Setup: Overview",
    "Plone Site Setup: Search",
    "Plone Site Setup: Security",
    "Plone Site Setup: Site",
    "Plone Site Setup: Themes",
    "Plone Site Setup: TinyMCE",
    "Plone Site Setup: Types",
    "Plone Site Setup: Users and Groups",
]


def rolemap_site_admin(context):
    """Add Site Administrator role to various permissions.

    Especially for control panels, permissions were defined in Python or zcml
    with both Manager and Site Administrator in the roles.
    On startup, this is set on the Zope level, NOT the Plone level.
    And on the Zope level the Site Administrator role is not defined.
    This works, but can give problems.
    So setting the Site Administrator role was moved to rolemap.xml
    See https://github.com/plone/Products.CMFPlone/pull/3225

    That works for new sites, but migrated sites now had a problem.
    Site Administrators lost all those permissions, and could not even
    see the Site Setup.  How to fix that?  Here we more or less follow this plan:
    https://github.com/plone/Products.CMFPlone/pull/3225#issuecomment-1467095416
    Not entirely though.  What we do for real, is described in inline comments below.
    """
    portal = getSite()
    for perm in portal.ac_inherited_permissions(1):
        # perm is a tuple: name, value, inherited roles.
        # ('Plone Site Setup: Editing', (), ('Manager',))
        name, value = perm[:2]
        for permission in SITE_ADMIN_PERMISSIONS:
            if name == permission:
                perm = Permission(name, value, portal)
                # getRoles gives the roles set on the current level (Plone),
                # so not inherited from Zope.
                # Note: when nothing is set explicitly, you still get ['Manager'].
                roles = perm.getRoles()
                if SITE_ADMIN in roles:
                    # nothing to do
                    continue
                # If roles is a list, then it is acquired.
                # It roles is a tuple, then it is not acquired.
                # If the permission is NOT acquired, this means that the user
                # has explicitly switched this off.  We leave it alone then.
                acquired = isinstance(roles, list)
                if acquired:
                    # This is the main thing we want to change:
                    # add Site Administrator to the roles on Plone level.
                    roles.append(SITE_ADMIN)
                    perm.setRoles(roles)
                    logger.info("Added %s role to '%s' permission.", SITE_ADMIN, name)
