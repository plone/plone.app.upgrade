from plone.app.upgrade.tests.base import MigrationTest


class TestAddSmtpImplicitTls(MigrationTest):
    def setUp(self):
        super().setUp()
        from plone.registry.interfaces import IRegistry
        from zope.component import getUtility

        self.registry = getUtility(IRegistry)
        # Simulate a site from before 6301.
        if "plone.smtp_implicit_tls" in self.registry.records:
            del self.registry.records["plone.smtp_implicit_tls"]

    def upgrade(self):
        from plone.app.upgrade.v63.alpha import add_smtp_implicit_tls

        add_smtp_implicit_tls(self.portal.portal_setup)

    def test_adds_record(self):
        self.registry["plone.smtp_host"] = "smtp.example.org"
        self.registry["plone.smtp_port"] = 465
        self.upgrade()
        self.assertFalse(self.registry["plone.smtp_implicit_tls"])
        # The other settings keep their values.
        self.assertEqual(self.registry["plone.smtp_host"], "smtp.example.org")
        self.assertEqual(self.registry["plone.smtp_port"], 465)
