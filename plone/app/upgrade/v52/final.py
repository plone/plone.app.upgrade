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


def move_dotted_to_named_behaviors(context):
    """named behaviors are better then dotted behaviors > let's move them."""
    from plone import api
    from plone.behavior.registration import lookup_behavior_registration
    from plone.dexterity.interfaces import IDexterityFTI

    ptt = api.portal.get_tool('portal_types')

    ftis = [fti for fti in ptt.objectValues() if IDexterityFTI.providedBy(fti)]

    for fti in ftis:
        behaviors = []
        for behavior in fti.behaviors:
            behavior_registration = lookup_behavior_registration(behavior)
            named_behavior = behavior_registration.name
            if named_behavior:
                behaviors.append(named_behavior)
                if named_behavior == behavior:
                    logger.info(
                        'Behavior "{behavior}" already named.'.format(
                            behavior=behavior,
                        ),
                    )
                else:
                    logger.info(
                        'Moved "{dotted}" to "{named}"'.format(
                            dotted=behavior,
                            named=named_behavior,
                        ),
                    )
            else:
                behaviors.append(behavior)
                logger.info(
                    '"{dotted}" has no name registered. '
                    'kept it dotted.'.format(
                        dotted=behavior,
                    ),
                )
        fti.behaviors = tuple(behaviors)
        logger.info(
            'Converted dotted behaviors of {ct} to named behaviors.'.format(
                ct=fti.title,
            ),
        )

    logger.info('Done moving dotted to named behaviors.')