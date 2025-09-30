from plone.registry.interfaces import IRegistry
from zope.component import getUtility

import json
import logging


logger = logging.getLogger(__name__)


def update_tinymce_toolbar_menu_styles(context):
    registry = getUtility(IRegistry)

    # rename "styleselect" to "styles"
    mce_toolbar = registry.records["plone.toolbar"].value
    registry["plone.toolbar"] = mce_toolbar.replace("styleselect", "styles")

    # rename "formats" to "styles"
    mce_menu = json.loads(registry.records["plone.menu"].value)

    try:
        mce_menu["format"]["items"] = mce_menu["format"]["items"].replace(
            "formats", "styles"
        )
        registry["plone.menu"] = json.dumps(mce_menu, indent=4)
    except KeyError:
        # in case of a custom tinymce menu configuration
        logger.info(
            "Could not rename 'formats' to 'styles' in 'plone.menu' registry value due to custom TinyMCE menu configuration"
        )
