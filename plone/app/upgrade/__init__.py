import pkg_resources
import sys
from zope.interface import implements
from Products.CMFQuickInstallerTool.interfaces import INonInstallable
from plone.app.upgrade import bbb
from plone.app.upgrade.utils import alias_module


class HiddenProducts(object):
    """This hides the upgrade profiles from the quick installer tool."""
    implements(INonInstallable)

    def getNonInstallableProducts(self):
        return [
            'plone.app.upgrade.v25',
            'plone.app.upgrade.v30',
            'plone.app.upgrade.v31',
            'plone.app.upgrade.v32',
            'plone.app.upgrade.v33',
            'plone.app.upgrade.v40',
            'plone.app.upgrade.v41',
            'plone.app.upgrade.v42',
            'plone.app.upgrade.v43',
            ]

# Make sure folks upgrading from Plone 2.1 see a helpful message telling them
# how to do a two-stage upgrade, instead of a GroupUserFolder error.
try:
    from Products.GroupUserFolder.GroupUserFolder import GroupUserFolder
except ImportError:
    from plone.app.upgrade import gruf_bbb
    sys.modules['Products.GroupUserFolder'] = gruf_bbb
    sys.modules['Products.GroupUserFolder.GroupUserFolder'] = gruf_bbb


try:
    from zope.app.cache.interfaces.ram import IRAMCache
except ImportError:
    import zope.ramcache.interfaces.ram
    alias_module('zope.app.cache.interfaces.ram', zope.ramcache.interfaces.ram)
    import zope.ramcache.ram
    alias_module('zope.app.cache.ram', zope.ramcache.ram)

if 'products.kupu' not in pkg_resources.working_set.by_key:
    import kupu_bbb
    alias_module('Products.kupu.plone.plonelibrarytool', kupu_bbb)


try:
    from Products.CMFPlone import UndoTool
except ImportError:    
    sys.modules['Products.CMFPlone.UndoTool'] = bbb


try:
    import Products.CMFActionIcons
except ImportError:
    alias_module('Products.CMFPlone.ActionIconsTool', bbb)
    alias_module('Products.CMFActionIcons.interfaces', bbb)
    alias_module('Products.CMFActionIcons.interfaces._tools', bbb)
    alias_module('Products.CMFActionIcons.ActionIconsTool', bbb)
