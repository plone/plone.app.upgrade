import logging
import re
from Acquisition import aq_get
from Products.CMFCore.utils import getToolByName
from Products.ZCatalog.ProgressHandler import ZLogHandler
from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.v40.alphas import cleanUpToolRegistry
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
            if hasattr(rids, 'keys'):
                change.extend(list(rids.keys()))
            else:
                change.append(rids)
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
        except (AttributeError, KeyError):
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
            index_id = index.getId()
            logger.info("Reindex %s index with I18N Case Normalizer",\
                        index_id)
            catalog.manage_clearIndex([index_id])
            catalog.reindexIndex(index_id,\
                                 aq_get(context, 'REQUEST', None))
        pass

def upgradeTinyMCE(context):
    """ Upgrade TinyMCE WYSIWYG Editor to jQuery based version 1.3

    This is profile version 4.
    """
    try:
        # Is the package still there?  Not on Plone 5.
        import Products.TinyMCE.upgrades
        Products.TinyMCE.upgrades  # pyflakes
    except ImportError:
        return
    context.upgradeProfile('Products.TinyMCE:TinyMCE', dest='4')


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
    """ Upgrade plone.app.jquery to profile version 3.
    """
    try:
        # Is the package still there?  Not on Plone 5.
        import plone.app.jquery
        plone.app.jquery  # pyflakes
    except ImportError:
        return
    context.upgradeProfile('plone.app.jquery:default', dest='3')


def to43alpha1(context):
    """4.2 -> 4.3alpha1"""
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v43:to43alpha1')
    reindex_sortable_title(context)
    upgradeTinyMCE(context)
    upgradePloneAppTheming(context)
    upgradePloneAppJQuery(context)


def upgradeSyndication(context):
    from zope.component import getUtility, getSiteManager
    from plone.registry.interfaces import IRegistry
    from Products.CMFCore.interfaces import ISyndicationTool
    from Products.CMFPlone.interfaces.syndication import ISyndicatable
    from Products.CMFPlone.interfaces.syndication import (
        ISiteSyndicationSettings, IFeedSettings)

    portal = getToolByName(context, 'portal_url').getPortalObject()

    def getDexterityFolderTypes():
        try:
            from plone.dexterity.interfaces import IDexterityFTI
            from plone.dexterity.utils import resolveDottedName
        except ImportError:
            return set([])

        portal_types = getToolByName(portal, 'portal_types')
        types = [fti for fti in portal_types.listTypeInfo() if
                    IDexterityFTI.providedBy(fti)]

        ftypes = set([])
        for _type in types:
            klass = resolveDottedName(_type.klass)
            if ISyndicatable.implementedBy(klass):
                ftypes.add(_type.getId())
        return ftypes

    logger.info('Migrating syndication tool')
    registry = getUtility(IRegistry)
    synd_settings = registry.forInterface(ISiteSyndicationSettings)
    # default settings work fine here if all settings are not
    # available
    try:
        old_synd_tool = portal.portal_syndication
        try:
            synd_settings.allowed = old_synd_tool.isAllowed
        except AttributeError:
            pass
        try:
            synd_settings.max_items = old_synd_tool.max_items
        except AttributeError:
            pass
        portal.manage_delObjects(['portal_syndication'])
    except AttributeError:
        pass
    sm = getSiteManager()
    sm.unregisterUtility(provided=ISyndicationTool)
    # now, go through all containers and look for syndication_info
    # objects
    catalog = getToolByName(portal, 'portal_catalog')
    # get all folder types from portal_types
    at_tool = getToolByName(portal, 'archetype_tool')
    folder_types = set([])
    for _type in at_tool.listPortalTypesWithInterfaces([ISyndicatable]):
        folder_types.add(_type.getId())
    folder_types = folder_types | getDexterityFolderTypes()
    for brain in catalog(portal_type=tuple(folder_types)):
        try:
            obj = brain.getObject()
        except (AttributeError, KeyError):
            continue
        if 'syndication_information' in obj.objectIds():
            # just having syndication info object means
            # syndication is enabled
            info = obj.syndication_information
            try:
                settings = IFeedSettings(obj)
            except TypeError:
                continue
            settings.enabled = True
            try:
                settings.max_items = info.max_items
            except AttributeError:
                pass
            settings.feed_types = ('RSS',)
            obj.manage_delObjects(['syndication_information'])


def to43alpha2(context):
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v43:to43alpha2')


def removeKSS(context):
    # remove KSS-related skin layers from all skins
    skinstool = getToolByName(context, 'portal_skins')
    selections = skinstool._getSelections()
    for skin_name in selections.keys():
        layers = selections[skin_name].split(',')
        if 'plone_kss' in layers:
            layers.remove('plone_kss')
        if 'archetypes_kss' in layers:
            layers.remove('archetypes_kss')
        skinstool.addSkinSelection(skin_name, ','.join(layers))

    # remove portal_kss tool
    portal = getToolByName(context, 'portal_url').getPortalObject()
    if 'portal_kss' in portal:
        portal.manage_delObjects(['portal_kss'])

    # make sure portal_kss is no longer listed as a required tool
    cleanUpToolRegistry(context)

    # make sure plone.app.kss is not activated in the quick installer
    qi = getToolByName(context, 'portal_quickinstaller')
    if qi.isProductInstalled('plone.app.kss'):
        qi.uninstallProduct('plone.app.kss')


def upgradeTinyMCEAgain(context):
    try:
        # Is the package still there?  Not on Plone 5.
        import Products.TinyMCE.upgrades
        Products.TinyMCE.upgrades  # pyflakes
    except ImportError:
        return
    context.upgradeProfile('Products.TinyMCE:TinyMCE')
