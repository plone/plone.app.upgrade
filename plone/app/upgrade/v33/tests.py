from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.tests.base import FunctionalUpgradeTestCase
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

class TestFunctionalMigrations(FunctionalUpgradeTestCase):

    def testBaseUpgrade(self):
        self.importFile(__file__, 'test-base.zexp')
        oldsite, result = self.migrate()

        mig = oldsite.portal_migration
        self.failIf(mig.needUpgrading())

        diff = self.export()
        len_diff = len(diff.split('\n'))
        # self.failUnless(len_diff <= 2500)

    def testFullUpgrade(self):
        self.importFile(__file__, 'test-full.zexp')
        oldsite, result = self.migrate()

        mig = oldsite.portal_migration
        self.failIf(mig.needUpgrading())

        diff = self.export()
        len_diff = len(diff.split('\n'))
        # self.failUnless(len_diff <= 2700)

    def testFolderUpgrade(self):
        from plone.folder.interfaces import IOrderableFolder
        self.importFile(__file__, 'test-full.zexp')
        # `portal_type` and `Type` can be checked before migration...
        oldsite = getattr(self.app, self.site_id)
        ids = 'news', 'events', 'Members'
        for id in ids:
            obj = oldsite[id]
            self.assertEquals(obj.portal_type, 'Large Plone Folder')
            self.assertEquals(obj.Type(), 'Large Folder')
            brain, = oldsite.portal_catalog(getId=id)   # asserts only one
            self.assertEquals(brain.portal_type, 'Large Plone Folder')
            self.assertEquals(brain.Type, 'Large Folder')
        # now let's migrate...
        oldsite, result = self.migrate()
        self.failIf(oldsite.portal_migration.needUpgrading())
        # after migration `/news`, `/events` and `/Members` are based on
        # `plone.(app.)folder`, but still have no ordering set...
        for id in ids:
            obj = oldsite[id]
            self.failUnless(IOrderableFolder.providedBy(obj),
                '%s not orderable?' % id)
            self.assertEquals(obj._ordering, 'unordered',
                '%s has no `_ordering`?' % id)
            self.assertEquals(obj.portal_type, 'Folder')
            self.assertEquals(obj.Type(), 'Folder')
            brain, = oldsite.portal_catalog(getId=id)   # asserts only one
            self.assertEquals(brain.portal_type, 'Folder')
            self.assertEquals(brain.Type, 'Folder')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestMigrations_v3_3))
    suite.addTest(makeSuite(TestFunctionalMigrations))
    return suite
