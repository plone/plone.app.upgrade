from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.tests.base import MigrationTest
from plone.app.upgrade.v33 import three2_three3

class TestMigrations_v3_3(MigrationTest):

    def afterSetUp(self):
        self.types = self.portal.portal_types
        self.properties = getToolByName(self.portal, 'portal_properties')
    
    def _upgrade(self):
        three2_three3(self.portal)
    
    def testRedirectLinksProperty(self):
        del self.properties.site_properties.redirect_links
        self._upgrade()
        self.assertEquals(True, 
            self.properties.site_properties.getProperty('redirect_links'))
    
    def testLinkDefaultView(self):
        self.types.Link.default_view = 'link_view'
        self.types.Link.immediate_view = 'link_view'
        self.types.Link.view_methods = ('link_view',)
        self._upgrade()
        self.assertEqual(self.types.Link.default_view, 'link_redirect_view')
        self.assertEqual(self.types.Link.immediate_view, 'link_redirect_view')
        self.assertEqual(self.types.Link.view_methods, ('link_redirect_view',))
        
    def testCustomizedLinkDefaultView(self):
        # but only change if old default was 'link_view'
        self.types.Link.default_view = 'foobar'
        self.types.Link.immediate_view = 'foobar'
        self.types.Link.view_methods = ('foobar',)
        self._upgrade()
        self.assertEqual(self.types.Link.default_view, 'foobar')
        self.assertEqual(self.types.Link.immediate_view, 'foobar')
        self.assertEqual(self.types.Link.view_methods, ('foobar',))

def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestMigrations_v3_3))
    return suite
