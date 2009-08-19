from zope.interface import implements
from Products.CMFQuickInstallerTool.interfaces import INonInstallable

class HiddenProducts(object):
    implements(INonInstallable)

    def getNonInstallableProducts(self):
        return [
            'plone.app.upgrade.v25',
            'plone.app.upgrade.v30',
            'plone.app.upgrade.v31',
            'plone.app.upgrade.v32',
            'plone.app.upgrade.v33',
            'plone.app.upgrade.v40',
            ]
