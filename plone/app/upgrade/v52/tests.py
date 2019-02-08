# -*- coding: utf-8 -*-

from plone.app.upgrade.v52.testing import REAL_UPGRADE_FUNCTIONAL
from plone.testing.z2 import Browser
from pkg_resources import get_distribution

import unittest


def test_suite():
    suite = unittest.TestSuite()
    return suite
