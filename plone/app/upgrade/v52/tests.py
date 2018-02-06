# -*- coding: utf-8 -*-
from plone.app.testing import PLONE_INTEGRATION_TESTING
from plone.app.upgrade.v50.testing import REAL_UPGRADE_FUNCTIONAL
from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from Products.CMFPlone.interfaces import IFilterSchema

import unittest

try:
    from Products.CMFPlone.factory import _IMREALLYPLONE5
    _IMREALLYPLONE5  # pyflakes
except ImportError:
    PLONE_5 = False
else:
    PLONE_5 = True



def test_suite():
    # Skip these tests on Plone 4
    if not PLONE_5:
        return unittest.TestSuite()

    suite = unittest.TestSuite()
    return suite
