from plone.base.interfaces import IMailSchema
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import logging

logger = logging.getLogger(__name__)


def add_smtp_implicit_tls(context):
    """Add the mail setting smtp_implicit_tls, keeping the other values."""
    registry = getUtility(IRegistry)
    registry.registerInterface(IMailSchema, prefix="plone")
    logger.info("Added the mail setting smtp_implicit_tls.")
