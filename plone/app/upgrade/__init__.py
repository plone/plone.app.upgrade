import sys
from zope.interface import implements
from Products.CMFQuickInstallerTool.interfaces import INonInstallable

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
            ]

# Make sure folks upgrading from Plone 2.1 see a helpful message telling them
# how to do a two-stage upgrade, instead of a GroupUserFolder error.
try:
    from Products.GroupUserFolder.GroupUserFolder import GroupUserFolder
except ImportError:
    from plone.app.upgrade import gruf_bbb
    sys.modules['Products.GroupUserFolder'] = gruf_bbb
    sys.modules['Products.GroupUserFolder.GroupUserFolder'] = gruf_bbb
