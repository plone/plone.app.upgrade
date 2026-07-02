from plone.base.utils import get_installer
from Products.CMFCore.utils import getToolByName

import logging

logger = logging.getLogger(__name__)


def manage_comments_icon(context):
    """if plone.app.discussion is installed, set the manage-comments action icon
    expression from its default to the bootstrap based new-style icons
    """

    installer = get_installer(context)
    if installer.is_product_installed("plone.app.discussion"):
        portal_actions = getToolByName(context, "portal_actions")
        user_actions = getattr(portal_actions, "user", None)
        if user_actions is not None:
            review_comments_action = getattr(user_actions, "review-comments", None)
            if review_comments_action is not None:
                # Check whether the action keeps its original state
                if (
                    review_comments_action.icon_expr
                    == "string:${globals_view/navigationRootUrl}/discussionitem_icon.png"
                ):
                    review_comments_action.icon_expr = "string:chat"
                    logger.info("Action icon modified for manage comments action")
                else:
                    logger.info(
                        "Manage comments action icon expression was modified by the user"
                    )
            else:
                logger.info("There is no manage comments action")
        else:
            logger.info("There are no user actions")
    else:
        logger.info("plone.app.discussion is not installed. Nothing is done.")
