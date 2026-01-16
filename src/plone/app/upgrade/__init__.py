from importlib.metadata import distribution
from importlib.metadata import PackageNotFoundError
from plone.app.upgrade.utils import alias_module


try:
    distribution("Products.CMFQuickInstallerTool")
except PackageNotFoundError:
    # The alias module helps when migrating to Plone 6.0.0a1.
    # Remove when we no longer support upgrading from Plone 5.2.
    from . import bbb_qi

    alias_module("Products.CMFQuickInstallerTool", bbb_qi)
    alias_module("Products.CMFPlone.QuickInstallerTool", bbb_qi)


class HiddenProducts:
    """This hides the upgrade profiles from the quick installer tool."""

    def getNonInstallableProducts(self):
        return [
            "plone.app.upgrade.v52",
            "plone.app.upgrade.v60",
            "plone.app.upgrade.v61",
        ]

    def getNonInstallableProfiles(self):
        return []
