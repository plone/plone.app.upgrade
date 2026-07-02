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
                    logger.info("Manage comments action icon modified")
                else:
                    logger.info(
                        "Manage comments action icon was modified by the user. Nothing is done."
                    )
            else:
                logger.info("There is no manage comments action. Nothing is done.")
        else:
            logger.info("There are no user actions. Nothing si done.")
    else:
        logger.info("plone.app.discussion is not installed. Nothing is done.")
