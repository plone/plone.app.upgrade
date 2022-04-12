from zope.interface import Interface


class INonInstallable(Interface):
    def getNonInstallableProducts():
        """Returns a list of products that should not be available for
        installation.
        """
