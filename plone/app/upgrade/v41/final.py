import logging

from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.utils import installOrReinstallProduct
from Products.CMFCore.utils import getToolByName
from Products.ZCTextIndex.OkapiIndex import OkapiIndex
from BTrees.Length import Length

logger = logging.getLogger('plone.app.upgrade')


def fixOkapiIndexes(catalog):
    # recalculate the _totaldoclen of OkapiIndexes, because there were some
    # releases of ZCTextIndex in the wild that let it get out of whack
    for index in catalog.getIndexObjects():
        index = getattr(index, 'index', index)
        if isinstance(index, OkapiIndex):
            index._totaldoclen = Length(long(sum(index._docweight.values())))


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


def to411(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:4.1-4.1.1')

    catalog = getToolByName(context, 'portal_catalog')
    fixOkapiIndexes(catalog)


def to412(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:4.1.1-4.1.2')


def to412_owner_tuples(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    fixOwnerTuples(portal)


def to413(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:4.1.2-4.1.3')


def to414(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:4.1.3-4.1.4')


def to415_discussion(context):
    portal = getToolByName(context, 'portal_url').getPortalObject()
    installPloneAppDiscussion(portal)


def to415(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:4.1.4-4.1.5')


def to416(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v41:4.1.5-4.1.6')
