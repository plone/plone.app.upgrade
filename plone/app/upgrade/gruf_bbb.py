from persistent import Persistent
from Products.Five import BrowserView

class UpgradeProcessError(Exception):
    """Two-stage upgrade required."""

class GroupUserFolder(Persistent):
    """Dummy GRUF for the purpose of raising our exception
       when its iterator is called by the ZPublisher validation hook
    """
    def __iter__(self):
        raise UpgradeProcessError

class UpgradeProcessErrorView(BrowserView):

    def __call__(self):
        return ('Upgrades from Plone < 2.5 are not supported. Please do a '
                'two-stage upgrade by upgrading to Plone 3 first. See '
                '<a href="http://plone.org/upgrade">the upgrade '
                'manual</a> for details.')
