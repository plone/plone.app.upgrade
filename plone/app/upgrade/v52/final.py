# -*- coding: utf-8 -*-
from zope.component import getUtility

import logging


logger = logging.getLogger('plone.app.upgrade')


def rebuild_redirections(context):
    """Rebuild the plone.app.redirector information.

    This initializes the date and manual information.
    """
    from plone.app.redirector.interfaces import IRedirectionStorage

    storage = getUtility(IRedirectionStorage)
    if not hasattr(storage, '_rebuild'):
        logger.warning(
            'Not rebuilding redirections: '
            'IRedirectionStorage misses the _rebuild method. '
        )
        return
    logger.info(
        'Starting rebuild of redirections to '
        'add date and manual information.'
    )
    storage._rebuild()
    logger.info('Done rebuilding redirections.')
