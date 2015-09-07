from zope.component import getAdapters, queryMultiAdapter
from zope.contentprovider.interfaces import IContentProvider
from zope.viewlet.interfaces import IViewlet

from plone.app.upgrade.tests.base import MigrationTest
from plone.app.upgrade.utils import loadMigrationProfile
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import getFSVersionTuple

import alphas

PLONE5 = getFSVersionTuple()[0] >= 5


class TestMigrations_v4_3alpha1(MigrationTest):

    profile = 'profile-plone.app.upgrade.v43:to43alpha1'

    def testProfile(self):
        # This tests the whole upgrade profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.assertTrue(True)

    def testAddDisplayPublicationDateInBylineProperty(self):
        if PLONE5:
            return
        pprop = getToolByName(self.portal, 'portal_properties')
        self.assertEqual(
            pprop.site_properties.getProperty('displayPublicationDateInByline'),
            False)

    def testUpgradeToI18NCaseNormalizer(self):
        from Products.CMFPlone.UnicodeSplitter.splitter import Splitter, CaseNormalizer
        ctool = self.portal.portal_catalog
        ctool.plone_lexicon._pipeline[1] == (Splitter(), CaseNormalizer())
        alphas.upgradeToI18NCaseNormalizer(self.portal.portal_setup)
        self.assertEqual(ctool.plone_lexicon._pipeline[1].__class__.__name__, 'I18NNormalizer')

    def testUpgradeTinyMCE(self):
        # skip test in new Plones that don't install tinymce to begin with
        if 'portal_tinymce' not in self.portal:
            return

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
        if not PLONE5:
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
        self.assertEqual(
            catalog(id=portal['num-title'].id)[0].Title,
            '10 green bottles, hanging on the wall',
        )
        self.assertEqual(
            catalog(id=portal['accidentally-fall'].id)[0].Title,
            'And if one green bottle should accidentally fall',
        )

        # Only the numerical title got reindexed
        portal.portal_setup.runAllImportStepsFromProfile('profile-plone.app.theming:default')
        alphas.reindex_sortable_title(portal.portal_setup)
        self.assertEqual(
            catalog(id=portal['num-title'].id)[0].Title,
            '9 green bottles, hanging on the wall'
        )
        self.assertEqual(
            catalog(id=portal['accidentally-fall'].id)[0].Title,
            'And if one green bottle should accidentally fall',
        )


class TestMigrations_v4_3final_to4308(MigrationTest):

    def testAddDefaultPlonePasswordPolicy(self):
        # this add the 'Default Plone Password Policy' to Plone's acl_users
        portal = self.portal
        # make sure the 'Default Plone Password Policy' does not exist in acl_users
        portal.acl_users.manage_delObjects(ids=['password_policy', ])
        self.assertFalse('password_policy' in portal.acl_users.objectIds())
        # find the relevant upgrade step and execute it
        from Products.GenericSetup.upgrade import listUpgradeSteps
        relevantStep = [step for step in listUpgradeSteps(portal.portal_setup, \
                                                          'Products.CMFPlone:plone',
                                                          '4307')[0] if
                        step['title'] == u'Add default Plone password policy'][0]
        # execute the step
        relevantStep['step'].handler(portal)
        # now it has been added...
        self.assertTrue('password_policy' in portal.acl_users.objectIds())
