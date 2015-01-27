from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.tests.base import FunctionalUpgradeTestCase
from plone.app.upgrade.tests.base import MigrationTest
from plone.app.upgrade.v33 import three2_three3
from plone.app.upgrade.utils import version_match


class TestMigrations_v3_3(MigrationTest):

    def afterSetUp(self):
        self.types = self.portal.portal_types
        self.properties = getToolByName(self.portal, 'portal_properties')

    def _upgrade(self):
        three2_three3(self.portal)

    def testRedirectLinksProperty(self):
        del self.properties.site_properties.redirect_links
        self._upgrade()
        self.assertEqual(True,
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
        self.assertFalse(mig.needUpgrading())

    def testFullUpgrade(self):
        self.importFile(__file__, 'test-full.zexp')
        oldsite, result = self.migrate()

        mig = oldsite.portal_migration
        self.assertFalse(mig.needUpgrading())

    def testFolderUpgrade(self):
        from plone.folder.interfaces import IOrderableFolder
        self.importFile(__file__, 'test-full.zexp')
        # `portal_type` and `Type` can be checked before migration...
        oldsite = getattr(self.app, self.site_id)
        ids = 'news', 'events', 'Members'
        for id in ids:
            obj = oldsite[id]
            self.assertEqual(obj.portal_type, 'Large Plone Folder')
            self.assertEqual(obj.Type(), 'Large Folder')
            brain, = oldsite.portal_catalog(getId=id)   # asserts only one
            self.assertEqual(brain.portal_type, 'Large Plone Folder')
            self.assertEqual(brain.Type, 'Large Folder')
        # now let's migrate...
        oldsite, result = self.migrate()
        self.assertFalse(oldsite.portal_migration.needUpgrading())
        # after migration `/news`, `/events` and `/Members` are based on
        # `plone.(app.)folder`, but still have no ordering set...
        for id in ids:
            obj = oldsite[id]
            self.assertTrue(IOrderableFolder.providedBy(obj),
                '%s not orderable?' % id)
            self.assertEqual(obj._ordering, 'unordered',
                '%s has no `_ordering`?' % id)
            self.assertEqual(obj.portal_type, 'Folder')
            self.assertEqual(obj.Type(), 'Folder')
            brain, = oldsite.portal_catalog(getId=id)   # asserts only one
            self.assertEqual(brain.portal_type, 'Folder')
            self.assertEqual(brain.Type, 'Folder')


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    if not version_match('3.3'):
        return suite
    suite.addTest(makeSuite(TestMigrations_v3_3))
    suite.addTest(makeSuite(TestFunctionalMigrations))
    return suite
