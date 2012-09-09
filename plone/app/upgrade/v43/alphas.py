import logging
import re
from Acquisition import aq_get
from Products.CMFCore.utils import getToolByName
from Products.ZCatalog.ProgressHandler import ZLogHandler
from plone.app.upgrade.utils import loadMigrationProfile
from Products.ZCTextIndex.interfaces import IZCTextIndex

logger = logging.getLogger('plone.app.upgrade')
num_sort_regex = re.compile('\d+')


def reindex_sortable_title(context):
    from Products.CMFPlone.CatalogTool import MAX_SORTABLE_TITLE
    catalog = getToolByName(context, 'portal_catalog')
    _catalog = catalog._catalog
    indexes = _catalog.indexes
    sort_title_index = indexes.get('sortable_title', None)
    if sort_title_index is None:
        return
    from Products.PluginIndexes.FieldIndex import FieldIndex
    if not isinstance(sort_title_index, FieldIndex.FieldIndex):
        return
    change = []
    pghandler = ZLogHandler(10000)
    logger.info('Analyzing sortable_title index')
    pghandler.init('Analyzing sortable_title index', len(sort_title_index))
    for i, (name, rids) in enumerate(sort_title_index._index.iteritems()):
        pghandler.report(i)
        if len(name) > MAX_SORTABLE_TITLE or num_sort_regex.match(name):
            change.extend(list(rids.keys()))
    pghandler.finish()
    update_metadata = 'sortable_title' in _catalog.schema
    pghandler = ZLogHandler(1000)
    logger.info('Updating sortable_title index')
    pghandler.init('Updating sortable_title index', len(change))
    for i, rid in enumerate(change):
        pghandler.report(i)
        brain = _catalog[rid]
        try:
            obj = brain.getObject()
        except AttributeError:
            continue
        if update_metadata:
            obj.reindexObject()
        else:
            obj.reindexObject(idxs=['sortable_title'])
    pghandler.finish()
    logger.info('Updated `sortable_title` index.')


def upgradeToI18NCaseNormalizer(context):
    """Upgrade lexicon to I18N Case Normalizer
    """
    catalog = getToolByName(context, 'portal_catalog')
    for index in catalog.Indexes.objectValues():
        if IZCTextIndex.providedBy(index):
            logger.info("Reindex %s index with I18N Case Normalizer",\
                        index.getId())
            catalog.reindexIndex(index.getId(),\
                                 aq_get(context, 'REQUEST', None))
        pass

def upgradeTinyMCE(context):
    """ Upgrade TinyMCE WYSIWYG Editor to jQuery based version 1.3
    """
    from Products.TinyMCE.upgrades import upgrade_12_to_13
    upgrade_12_to_13(context)

def upgradePloneAppTheming(context):
    """Re-install plone.app.theming if previously installed
    """

    try:
        from plone.app.theming.interfaces import IThemeSettings
    except ImportError:
        # plone.app.theming is not in the build
        return

    from plone.registry.interfaces import IRegistry
    from zope.component import getUtility

    registry = getUtility(IRegistry)

    try:
        registry.forInterface(IThemeSettings)
    except KeyError:
        # plone.app.theming not installed
        return

    portal_setup = getToolByName(context, 'portal_setup')
    return portal_setup.runAllImportStepsFromProfile('profile-plone.app.theming:default')

def upgradePloneAppJQuery(context):
    """ Upgrade TinyMCE WYSIWYG Editor to jQuery based version 1.3
    """
    from plone.app.jquery.upgrades import upgrade_2_to_3
    upgrade_2_to_3(context)

def to43alpha1(context):
    """4.2 -> 4.3alpha1"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v43:to43alpha1')
    reindex_sortable_title(context)
    upgradeToI18NCaseNormalizer(context)
    upgradeTinyMCE(context)
    upgradePloneAppTheming(context)
    upgradePloneAppJQuery(context)


def upgradeSyndication(context):
    from zope.component import getUtility
    from plone.registry.interfaces import IRegistry
    from Products.CMFPlone.interfaces.syndication import (
        ISiteSyndicationSettings, IFeedSettings)

    logger.info('Migrating syndication tool')
    portal = getToolByName(context, 'portal_url').getPortalObject()
    old_synd_tool = portal.portal_syndication
    registry = getUtility(IRegistry)
    synd_settings = registry.forInterface(ISiteSyndicationSettings)
    synd_settings.allowed = old_synd_tool.isAllowed
    synd_settings.max_items = old_synd_tool.max_items
    portal.manage_delObjects(['portal_syndication'])
    # now, go through all containers and look for syndication_info
    # objects
    catalog = getToolByName(portal, 'portal_catalog')
    for brain in catalog(portal_type=('Topic', 'Collection', 'Folder',
                                      'Large Plone Folder')):
        obj = brain.getObject()
        if 'syndication_information' in obj.objectIds():
            # just having syndication info object means
            # syndication is enabled
            info = obj.syndication_information
            settings = IFeedSettings(obj)
            settings.enabled = True
            settings.max_items = info.max_items
            settings.feed_types = ('RSS',)
            obj.manage_delObjects(['syndication_information'])


def to43alpha2(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v43:to43alpha2')
    upgradeSyndication(context)
