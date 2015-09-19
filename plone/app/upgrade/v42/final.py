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
    qi = getToolByName(context, 'portal_quickinstaller')
    qi.upgradeProduct('Products.CMFEditions')


def to42final(context):
    """4.2rc2 -> 4.2 final
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v42:to42final')


def to421(context):
    """4.2 -> 4.2.1
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v42:to421')

def to422(context):
    """4.2.1 -> 4.2.2
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v42:to422')

def to423(context):
    """4.2.2 -> 4.2.3
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v42:to423')

def to424(context):
    """4.2.3 -> 4.2.4
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v42:to424')

def to425(context):
    """4.2.4 -> 4.2.5
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v42:to425')
