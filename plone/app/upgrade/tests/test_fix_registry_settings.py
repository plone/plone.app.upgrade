from plone.app.upgrade import utils
from plone.app.upgrade.tests.base import MigrationTest
from plone.base.interfaces.syndication import ISiteSyndicationSettings


class TestFixRegistrySettings(MigrationTest):
    
    def test_fix_syndication_settings(self):
        # add fake settings, simulate the old iface settings of
        # Products.CMFPlone.interfaces.syndication.ISiteSyndicationSettings 

        from plone.app.upgrade.v60.final import fix_syndication_settings
        from plone.registry.interfaces import IRegistry
        from zope.component import getUtility

        registry = getUtility(IRegistry)
        
        registry.registerInterface(
            ISiteSyndicationSettings,
            prefix="Products.CMFPlone.interfaces.syndication.ISiteSyndicationSettings"
        )
        
        records = list(registry.records.keys())
        
        old_iface = "Products.CMFPlone.interfaces.syndication.ISiteSyndicationSettings"
        new_iface ="plone.base.interfaces.syndication.ISiteSyndicationSettings"

        fieldnames=[
            "allowed",
            "default_enabled",
            "search_rss_enabled",
            "show_author_info",
            "render_body",
            "max_items",
            "allowed_feed_types",
            "site_rss_items",
            "show_syndication_button",
            "show_syndication_link"
        ]

        # test both fields from the new and the old interface are in the registry
        for fieldname in fieldnames:

            recordname = f"{old_iface}.{fieldname}"
            self.assertIn(recordname, records)
            
            recordname = f"{new_iface}.{fieldname}"
            self.assertIn(recordname, records)
        
        # remove the old fields and copy the record values
        fix_syndication_settings(self.portal)

        records = list(registry.records.keys())

        # test only fields from the new are in the registry
        for fieldname in fieldnames:

            recordname = f"{old_iface}.{fieldname}"
            self.assertNotIn(recordname, records)
            
            recordname = f"{new_iface}.{fieldname}"
            self.assertIn(recordname, records)
