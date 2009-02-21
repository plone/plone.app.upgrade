#
# Base TestCase for upgrades
#

from Products.PloneTestCase import ptc

from Products.CMFCore.interfaces import IActionCategory
from Products.CMFCore.interfaces import IActionInfo
from Products.CMFCore.utils import getToolByName

ptc.setupPloneSite()


class MigrationTest(ptc.PloneTestCase):
    pass
