# -*- coding: utf-8 -*-

from plone.app.upgrade.utils import plone_version
from plone.testing.z2 import Browser

import unittest


def test_suite():
    # Skip these tests on Plone 4
    if plone_version <= '5.0':
        return unittest.TestSuite()
    suite = unittest.TestSuite()
    return suite
