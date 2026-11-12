from plone.app.upgrade.tests.base import MigrationTest

OLD_LARGE = ["preview", "teaser", "large", "great", "huge"]


class TestAddLargerImageScales(MigrationTest):
    def setUp(self):
        super().setUp()
        from plone.registry.interfaces import IRegistry
        from zope.component import getUtility

        self.registry = getUtility(IRegistry)
        # Simulate a site from before 6301.
        self.registry["plone.allowed_sizes"] = ["huge 1600:65536", "mini 200:65536"]
        self.set_large_scales(OLD_LARGE)

    def set_large_scales(self, scales):
        variants = dict(self.registry["plone.picture_variants"])
        large = dict(variants["large"])
        large["sourceset"] = [dict(large["sourceset"][-1], additionalScales=scales)]
        variants["large"] = large
        self.registry["plone.picture_variants"] = variants

    def large_scales(self):
        variants = self.registry["plone.picture_variants"]
        return variants["large"]["sourceset"][-1]["additionalScales"]

    def upgrade(self):
        from plone.app.upgrade.v63.alpha import add_larger_image_scales

        add_larger_image_scales(self.portal.portal_setup)

    def test_adds_sizes(self):
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
        self.assertEqual(self.large_scales(), OLD_LARGE + ["fullhd", "qhd"])
        # Running it again changes nothing.
        self.upgrade()
        self.assertEqual(len(self.registry["plone.allowed_sizes"]), 4)
        self.assertEqual(self.large_scales(), OLD_LARGE + ["fullhd", "qhd"])

    def test_keeps_existing_sizes(self):
        # A site with its own scale of that name or width keeps it.
        sizes = ["fullhd 1900:1200", "wide 2560:65536", "huge 1600:65536"]
        self.registry["plone.allowed_sizes"] = list(sizes)
        self.upgrade()
        self.assertEqual(self.registry["plone.allowed_sizes"], sizes)
        # qhd was not added, so the picture variant is left alone.
        self.assertEqual(self.large_scales(), OLD_LARGE)

    def test_keeps_changed_picture_variant(self):
        scales = ["teaser", "huge"]
        self.set_large_scales(scales)
        self.upgrade()
        self.assertEqual(self.large_scales(), scales)
