from plone.app.upgrade.tests.base import MigrationTest


class TestUpgradeImagingSettings(MigrationTest):
    def setUp(self):
        super().setUp()
        from plone.registry.interfaces import IRegistry
        from zope.component import getUtility

        self.registry = getUtility(IRegistry)
        # Simulate a site from before 6301.
        if "plone.scale_format" in self.registry.records:
            del self.registry.records["plone.scale_format"]

    def upgrade(self):
        from plone.app.upgrade.v63.alpha import update_imaging_settings

        update_imaging_settings(self.portal.portal_setup)

    def test_adds_scale_format(self):
        quality = self.registry["plone.quality"] = 75
        self.upgrade()
        self.assertEqual(self.registry["plone.scale_format"], "original")
        # The other settings keep their values.
        self.assertEqual(self.registry["plone.quality"], quality)

    def test_adds_sizes(self):
        self.registry["plone.allowed_sizes"] = ["huge 1600:65536", "mini 200:65536"]
        self.upgrade()
        self.assertEqual(
            self.registry["plone.allowed_sizes"],
            [
                "qhd 2560:65536",
                "fullhd 1920:65536",
                "huge 1600:65536",
                "mini 200:65536",
            ],
        )
        # Running it again changes nothing.
        self.upgrade()
        self.assertEqual(len(self.registry["plone.allowed_sizes"]), 4)

    def test_keeps_existing_sizes(self):
        # A site with its own scale of that name or width keeps it.
        sizes = ["fullhd 1900:1200", "wide 2560:65536", "huge 1600:65536"]
        self.registry["plone.allowed_sizes"] = list(sizes)
        self.upgrade()
        self.assertEqual(self.registry["plone.allowed_sizes"], sizes)
