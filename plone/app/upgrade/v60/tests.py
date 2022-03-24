# -*- coding: utf-8 -*-
from plone.app.testing import PLONE_INTEGRATION_TESTING
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility

import unittest


class Various60Test(unittest.TestCase):
    layer = PLONE_INTEGRATION_TESTING

    def test_add_new_image_scales(self):
        from plone.app.upgrade.v60.alphas import add_new_image_scales

        # These new scales should get added:
        new_scales = [
            "teaser 600:65536",
            "larger 1000:65536",
            "great 1200:65536",
            "huge 1600:65536",
        ]
        portal = self.layer["portal"]
        setup = getToolByName(portal, "portal_setup")
        registry = getUtility(IRegistry)

        # Call the upgrade step.
        add_new_image_scales(setup)
        record = registry.records["plone.allowed_sizes"]
        for scale in new_scales:
            self.assertIn(scale, record.value)

        # If scales with the given name already exist, do not change them.
        record.value = [
            "mini 200:200",
            "teaser 42:42",
            "maxi 200:400",
        ]
        add_new_image_scales(setup)
        self.assertIn("mini 200:200", record.value)
        self.assertIn("teaser 42:42", record.value)
        self.assertNotIn("teaser 600:65536", record.value)
        self.assertIn("huge 1600:65536", record.value)

        # If we make a change, we sort by width, then height.
        self.assertEqual(
            record.value,
            [
                "huge 1600:65536",
                "great 1200:65536",
                "larger 1000:65536",
                "maxi 200:400",
                "mini 200:200",
                "teaser 42:42",
            ],
        )

        # If we do not make a change, we also do not change the sort order.
        # As value, store the new scales alphabetically ordered.
        record.value = sorted(new_scales)
        add_new_image_scales(setup)
        self.assertEqual(record.value, sorted(new_scales))

        # Check that the upgrade does not break easily.
        record.value = [
            "too many spaces 100:100",
            "not_enough_spaces200:200",
            "too_many_colons 300:300:400",
            "not_enough_many_colons 500",
            "good 600:600",
            " space 700:700 ",
            "# just a comment",
            "or an empty line:",
            "",
        ]
        # The biggest is is that this does not throw an error:
        add_new_image_scales(setup)
        # The bad scales will be at the end.
        self.assertEqual(
            record.value,
            [
                "huge 1600:65536",
                "great 1200:65536",
                "larger 1000:65536",
                " space 700:700 ",
                "teaser 600:65536",
                "good 600:600",
                "too many spaces 100:100",
                "not_enough_spaces200:200",
                "too_many_colons 300:300:400",
                "not_enough_many_colons 500",
                "# just a comment",
                "or an empty line:",
            ],
        )
