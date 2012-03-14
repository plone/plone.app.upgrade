import logging

from Acquisition import aq_get
from Products.CMFPlone.utils import getToolByName
from plone.app.upgrade.utils import loadMigrationProfile

from Products.ZCTextIndex.interfaces import IZCTextIndex

logger = logging.getLogger('plone.app.upgrade')


def upgradeToI18NCaseNormalizer(context):
    """Upgrade lexicon to I18N Case Normalizer
    """
    loadMigrationProfile(context, 'profile-plone.app.upgrade.v43:upgradeToI18NCaseNormalizer')
    catalog = getToolByName(context, 'portal_catalog')
    for index in catalog.Indexes.objectValues():
        if IZCTextIndex.providedBy(index):
            logger.info("Reindex %s index with I18N Case Normalizer", index.getId())
            catalog.reindexIndex(index.getId(), aq_get(context, 'REQUEST', None))
        pass
