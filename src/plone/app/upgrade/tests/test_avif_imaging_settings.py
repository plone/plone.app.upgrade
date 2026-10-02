from plone.app.upgrade.tests.base import MigrationTest
from plone.app.upgrade.v63.alpha import add_avif_imaging_settings
from plone.registry.interfaces import IRegistry
from zope.component import getUtility

AVIF_RECORDS = ("plone.avif_mode", "plone.avif_quality", "plone.avif_speed")


class TestAvifImagingSettings(MigrationTest):
    def test_adds_the_avif_records_with_their_defaults(self):
        registry = getUtility(IRegistry)
        for name in AVIF_RECORDS:
            del registry.records[name]
        registry["plone.quality"] = 77

        add_avif_imaging_settings(self.portal)

        self.assertEqual(registry["plone.avif_mode"], "avif_with_fallback")
        self.assertEqual(registry["plone.avif_quality"], 65)
        self.assertEqual(registry["plone.avif_speed"], 8)
        # Existing settings keep their values.
        self.assertEqual(registry["plone.quality"], 77)

    def test_keeps_a_chosen_avif_mode(self):
        registry = getUtility(IRegistry)
        registry["plone.avif_mode"] = "avif_only"

        add_avif_imaging_settings(self.portal)

        self.assertEqual(registry["plone.avif_mode"], "avif_only")
