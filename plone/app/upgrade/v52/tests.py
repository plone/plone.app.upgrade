# -*- coding: utf-8 -*-
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
