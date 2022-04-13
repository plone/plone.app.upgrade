from OFS.ObjectManager import ObjectManager
from OFS.SimpleItem import SimpleItem
from Products.CMFCore.utils import UniqueObject


# from Products.CMFQuickInstallerTool.interfaces import INonInstallable
# from Products.CMFQuickInstallerTool.interfaces import IQuickInstallerTool
# from zope.interface import implementer


# @implementer(INonInstallable)
class HiddenProducts:
    def getNonInstallableProducts(self):
        # We can't really install ourselves: that would be weird.
        # So hide ourselves from ourselves.
        return ["CMFQuickInstallerTool", "Products.CMFQuickInstallerTool"]


# @implementer(IQuickInstallerTool)
class QuickInstallerTool(UniqueObject, ObjectManager, SimpleItem):

    meta_type = "CMF QuickInstaller Tool"
    id = "portal_quickinstaller"
