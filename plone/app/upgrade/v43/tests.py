from zope.component import getAdapters, queryMultiAdapter
from zope.contentprovider.interfaces import IContentProvider
from zope.viewlet.interfaces import IViewlet

from Products.CMFCore.utils import getToolByName
from plone.app.upgrade.tests.base import MigrationTest
from plone.app.upgrade.utils import loadMigrationProfile

import alphas


class TestMigrations_v4_3alpha1(MigrationTest):

    profile = 'profile-plone.app.upgrade.v43:to43alpha1'

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.failUnless(True)

    def testAddDisplayPublicationDateInBylineProperty(self):
        pprop = getToolByName(self.portal, 'portal_properties')
        self.assertEquals(
            pprop.site_properties.getProperty('displayPublicationDateInByline'),
            False)

    def testUpgradeToI18NCaseNormalizer(self):
        from Products.CMFPlone.UnicodeSplitter.splitter import Splitter, CaseNormalizer
        ctool = self.portal.portal_catalog
        ctool.plone_lexicon._pipeline[1] == (Splitter(), CaseNormalizer())
        alphas.upgradeToI18NCaseNormalizer(self.portal.portal_setup)
        self.assertEqual(ctool.plone_lexicon._pipeline[1].__class__.__name__, 'I18NNormalizer')
        self.failUnless(len(ctool.searchResults(SearchableText="welcome")) > 0)

    def testUpgradeTinyMCE(self):
        alphas.upgradeTinyMCE(self.portal.portal_setup)
        jstool = getToolByName(self.portal, 'portal_javascripts')
        jsresourceids = jstool.getResourceIds()

        self.assertTrue('jquery.tinymce.js' in jsresourceids)
        for ne in ['tiny_mce.js', 'tiny_mce_init.js']:
            self.assertFalse(ne in jsresourceids)

        ksstool = getToolByName(self.portal, 'portal_kss', None)
        if ksstool is not None:
            kssresourceids = ksstool.getResourceIds()
            self.assertFalse(
                '++resource++tinymce.kss/tinymce.kss' in kssresourceids)

        request = self.app.REQUEST
        plone_view = queryMultiAdapter((self.portal, request), name="plone")
        manager = queryMultiAdapter(
                    (self.portal, request, plone_view), IContentProvider, 'plone.htmlhead')
        viewlets = getAdapters(
                (manager.context, manager.request, manager.__parent__, manager), IViewlet)
        self.assertFalse(u'tinymce.configuration' in dict(viewlets))

    def testInstallThemingNotPreviouslyInstalled(self):
        from plone.app.theming.interfaces import IThemeSettings
        from plone.registry.interfaces import IRegistry
        from zope.component import getUtility

        alphas.upgradePloneAppTheming(self.portal.portal_setup)

        registry = getUtility(IRegistry)
        self.assertRaises(KeyError, registry.forInterface, IThemeSettings)

    def testInstallThemingPreviouslyInstalled(self):
        from plone.app.theming.interfaces import IThemeSettings
        from plone.registry.interfaces import IRegistry
        from zope.component import getUtility

        self.portal.portal_setup.runAllImportStepsFromProfile('profile-plone.app.theming:default')
        alphas.upgradePloneAppTheming(self.portal.portal_setup)

        registry = getUtility(IRegistry)

        try:
            registry.forInterface(IThemeSettings)
        except KeyError:
            self.fail("plone.app.theming not installed")

    def testReindexNumericalTitle(self):
        from Products.CMFCore.utils import getToolByName

        # Create 2 pages, one with a numerical title
        portal = self.portal
        self.setRoles(["Manager"])
        catalog = getToolByName(portal, 'portal_catalog')
        portal.invokeFactory(
            id='num-title', type_name='Document',
            title='10 green bottles, hanging on the wall',
        )
        portal.invokeFactory(
            id='accidentally-fall', type_name='Document',
            title='And if one green bottle should accidentally fall',
        )

        # Change title of both, shouldn't be reindexed yet
        portal['accidentally-fall'].title = 'fell'
        portal['num-title'].title = '9 green bottles, hanging on the wall'
        self.assertEquals(
            catalog(id=portal['num-title'].id)[0].Title,
            '10 green bottles, hanging on the wall',
        )
        self.assertEquals(
            catalog(id=portal['accidentally-fall'].id)[0].Title,
            'And if one green bottle should accidentally fall',
        )

        # Only the numerical title got reindexed
        portal.portal_setup.runAllImportStepsFromProfile('profile-plone.app.theming:default')
        alphas.reindex_sortable_title(portal.portal_setup)
        self.assertEquals(
            catalog(id=portal['num-title'].id)[0].Title,
            '9 green bottles, hanging on the wall'
        )
        self.assertEquals(
            catalog(id=portal['accidentally-fall'].id)[0].Title,
            'And if one green bottle should accidentally fall',
        )
