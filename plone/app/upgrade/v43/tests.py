# -*- coding: utf-8 -*-
from plone.app.upgrade.tests.base import MigrationTest
from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.utils import plone_version
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.interfaces import INonInstallable
from Products.CMFPlone.utils import getFSVersionTuple
from Products.GenericSetup import profile_registry
from Products.GenericSetup.interfaces import EXTENSION
from zope.component import getAdapters
from zope.component import getSiteManager
from zope.component import queryMultiAdapter
from zope.contentprovider.interfaces import IContentProvider
from zope.interface import implementer
from zope.viewlet.interfaces import IViewlet
from . import alphas

import six
import unittest


try:
    from Products.CMFCore.indexing import processQueue
except ImportError:
    def processQueue():
        pass


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
            pprop.site_properties.getProperty(
                'displayPublicationDateInByline'),
            False)

    def testUpgradeToI18NCaseNormalizer(self):
        from Products.CMFPlone.UnicodeSplitter.splitter import Splitter
        from Products.CMFPlone.UnicodeSplitter.splitter import CaseNormalizer
        ctool = self.portal.portal_catalog
        ctool.plone_lexicon._pipeline[1] == (Splitter(), CaseNormalizer())
        alphas.upgradeToI18NCaseNormalizer(self.portal.portal_setup)
        self.assertEqual(ctool.plone_lexicon._pipeline[
                         1].__class__.__name__, 'I18NNormalizer')

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
        plone_view = queryMultiAdapter((self.portal, request), name='plone')
        manager = queryMultiAdapter(
            (self.portal, request, plone_view),
            IContentProvider,
            'plone.htmlhead')
        viewlets = getAdapters(
            (manager.context, manager.request, manager.__parent__, manager),
            IViewlet)
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

        self.portal.portal_setup.runAllImportStepsFromProfile(
            'profile-plone.app.theming:default')
        alphas.upgradePloneAppTheming(self.portal.portal_setup)

        registry = getUtility(IRegistry)

        try:
            registry.forInterface(IThemeSettings)
        except KeyError:
            self.fail('plone.app.theming not installed')

    def testReindexNumericalTitle(self):
        from Products.CMFCore.utils import getToolByName

        # Create 2 pages, one with a numerical title
        portal = self.portal
        self.setRoles(['Manager'])
        catalog = getToolByName(portal, 'portal_catalog')
        portal.invokeFactory(
            id='num-title', type_name='Document',
            title='10 green bottles, hanging on the wall',
        )
        portal.invokeFactory(
            id='accidentally-fall', type_name='Document',
            title='And if one green bottle should accidentally fall',
        )
        processQueue()

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
        portal.portal_setup.runAllImportStepsFromProfile(
            'profile-plone.app.theming:default')
        alphas.reindex_sortable_title(portal.portal_setup)
        self.assertEqual(
            catalog(id=portal['num-title'].id)[0].Title,
            '9 green bottles, hanging on the wall',
        )
        self.assertEqual(
            catalog(id=portal['accidentally-fall'].id)[0].Title,
            'And if one green bottle should accidentally fall',
        )


class TestMigrations_v4_3final_to4308(MigrationTest):

    def testAddDefaultPlonePasswordPolicy(self):
        # this add the 'Default Plone Password Policy' to Plone's acl_users
        portal = self.portal
        # make sure the 'Default Plone Password Policy' does not exist in
        # acl_users
        portal.acl_users.manage_delObjects(ids=['password_policy', ])
        self.assertFalse('password_policy' in portal.acl_users.objectIds())
        # find the relevant upgrade step and execute it
        from Products.GenericSetup.upgrade import listUpgradeSteps
        relevantStep = [step for step in listUpgradeSteps(
            portal.portal_setup, 'Products.CMFPlone:plone', '4307')[0] if
            step['title'] == u'Add default Plone password policy'][0]
        # execute the step
        relevantStep['step'].handler(portal)
        # now it has been added...
        self.assertTrue('password_policy' in portal.acl_users.objectIds())

@unittest.skipIf(plone_version >= '5.2', 'Plone >=5.2')
class TestFakeKupuMigration(MigrationTest):

    def afterSetUp(self):
        from plone.app.upgrade.kupu_bbb import PloneKupuLibraryTool
        portal = self.portal
        self.csstool = getToolByName(portal, 'portal_css')
        self.jstool = getToolByName(portal, 'portal_javascripts')
        self.control_panel = getToolByName(portal, 'portal_controlpanel')
        pprops = getToolByName(portal, 'portal_properties')
        self.site_properties = pprops.site_properties
        bad_expr = ('python:portal.kupu_library_tool.isKupuEnabled'
                    '(REQUEST=request)')
        allowed_expr = "python:'kupu_library_tool' not in portal"
        # Setup a fake kupu with resources and settings
        self.kupu_id = 'kupu_library_tool'
        portal._setObject(self.kupu_id, PloneKupuLibraryTool(id=self.kupu_id))
        self.csstool.registerStylesheet('somekupu.css', expression=bad_expr)
        self.csstool.registerStylesheet('nokupu.css', expression=allowed_expr)
        self.jstool.registerScript('somekupu.js', expression=bad_expr)
        self.jstool.registerScript('nokupu.js', expression=allowed_expr)
        self.control_panel.registerConfiglet('kupu', 'kupu', '')
        if self.site_properties.hasProperty('available_editors'):
            self.site_properties._updateProperty(
                'available_editors', ('TinyMCE', 'Kupu', ''))
        else:
            self.site_properties._setProperty(
                'available_editors', ('TinyMCE', 'Kupu', ''))
        if self.site_properties.hasProperty('default_editor'):
            self.site_properties._updateProperty('default_editor', 'Kupu')
        else:
            self.site_properties._setProperty('default_editor', 'Kupu')
        self.member_data = getToolByName(portal, 'portal_memberdata')
        if self.member_data.hasProperty('wysiwyg_editor'):
            self.member_data._updateProperty('wysiwyg_editor', 'Kupu')
        else:
            self.member_data._setProperty('wysiwyg_editor', 'Kupu')

    def testBeforeRemoveFakeKupu(self):
        # Test that our test setup has worked.
        self.assertTrue(self.kupu_id in self.portal)
        self.assertTrue(self.csstool.getResource('somekupu.css') is not None)
        self.assertTrue(self.csstool.getResource('nokupu.css') is not None)
        self.assertTrue(self.jstool.getResource('somekupu.js') is not None)
        self.assertTrue(self.jstool.getResource('nokupu.js') is not None)
        self.assertTrue(
            self.control_panel.getActionObject('Plone/kupu') is not None)
        self.assertTrue(
            'Kupu' in self.site_properties.getProperty('available_editors'))
        self.assertEqual(
            self.site_properties.getProperty('default_editor'), 'Kupu')
        self.assertEqual(
            self.member_data.getProperty('wysiwyg_editor'), 'Kupu')

    def testRemoveFakeKupu(self):
        from plone.app.upgrade.v43.final import removeFakeKupu
        # Call the upgrade
        setup = getToolByName(self.portal, 'portal_setup')
        removeFakeKupu(setup)
        # Test that the tool is gone
        self.assertTrue(self.kupu_id not in self.portal)
        # Assert that the bad resources are gone and the allowed ones
        # are still there.
        self.assertTrue(self.csstool.getResource('somekupu.css') is None)
        self.assertTrue(self.csstool.getResource('nokupu.css') is not None)
        self.assertTrue(self.jstool.getResource('somekupu.js') is None)
        self.assertTrue(self.jstool.getResource('nokupu.js') is not None)
        self.assertTrue(
            self.control_panel.getActionObject('Plone/kupu') is None)
        self.assertTrue(
            'Kupu' not in
            self.site_properties.getProperty('available_editors'))
        self.assertNotEqual(
            self.site_properties.getProperty('default_editor'), 'Kupu')
        self.assertNotEqual(
            self.member_data.getProperty('wysiwyg_editor'), 'Kupu')

    def testNoRemoveFakeKupu(self):
        # Test that we do nothing when the tool is there and is not an
        # instance of the fake class
        from OFS.SimpleItem import SimpleItem
        self.portal._delObject(self.kupu_id)
        self.portal._setObject(self.kupu_id, SimpleItem(id=self.kupu_id))
        from plone.app.upgrade.v43.final import removeFakeKupu
        # Call the upgrade
        setup = getToolByName(self.portal, 'portal_setup')
        removeFakeKupu(setup)
        self.assertTrue(self.kupu_id in self.portal)
        self.assertTrue(self.csstool.getResource('somekupu.css') is not None)
        self.assertTrue(self.csstool.getResource('nokupu.css') is not None)
        self.assertTrue(self.jstool.getResource('somekupu.js') is not None)
        self.assertTrue(self.jstool.getResource('nokupu.js') is not None)
        self.assertTrue(
            self.control_panel.getActionObject('Plone/kupu') is not None)
        self.assertTrue(
            'Kupu' in self.site_properties.getProperty('available_editors'))
        self.assertEqual(
            self.site_properties.getProperty('default_editor'), 'Kupu')
        self.assertEqual(
            self.member_data.getProperty('wysiwyg_editor'), 'Kupu')


class TestQIandGS(MigrationTest):

    def testUnmarkUnavailableProfiles(self):
        from plone.app.upgrade.v43.final import unmarkUnavailableProfiles
        setup = getToolByName(self.portal, 'portal_setup')
        profile_id = 'dummyxyz:default'
        # Pretend that this profile was installed at some point.
        setup.setLastVersionForProfile(profile_id, '1.0')
        self.assertTrue(profile_id in setup._profile_upgrade_versions)
        # The profile is not known to portal_setup: it is not
        # registered in zcml.  So our cleanup function gets rid of it.
        unmarkUnavailableProfiles(setup)
        self.assertFalse(profile_id in setup._profile_upgrade_versions)

    def testMarkProductsInstalledForUninstallableProfiles(self):
        from plone.app.upgrade.v43.final import \
            markProductsInstalledForUninstallableProfiles

        qi = getToolByName(self.portal, 'portal_quickinstaller', None)
        if qi is None:
            # Newer Plone without qi.
            return

        # Register a profile.
        product_id = 'my.test.package'
        profile_id = '{0}:default'.format(product_id)
        profile_registry.registerProfile(
            'default', 'title', 'description', '/my/path',
            product=product_id, profile_type=EXTENSION)

        # Hide the profile.
        @implementer(INonInstallable)
        class HiddenProfiles(object):

            def getNonInstallableProfiles(self):
                return [profile_id]

        sm = getSiteManager()
        sm.registerUtility(factory=HiddenProfiles, name='my.test.package')

        # Check that nothing is installed at first.
        setup = getToolByName(self.portal, 'portal_setup')
        self.assertEqual(
            setup.getLastVersionForProfile(profile_id), 'unknown')
        self.assertFalse(qi.isProductInstalled(product_id))

        # Call our upgrade function.  This should have no effect,
        # because the profile is not installed.
        markProductsInstalledForUninstallableProfiles(setup)
        self.assertEqual(
            setup.getLastVersionForProfile(profile_id), 'unknown')
        self.assertFalse(qi.isProductInstalled(product_id))

        # Now fake that the profile is installed and try again.
        setup.setLastVersionForProfile(profile_id, '1.0')
        markProductsInstalledForUninstallableProfiles(setup)
        self.assertEqual(
            setup.getLastVersionForProfile(profile_id), ('1', '0'))
        self.assertTrue(qi.isProductInstalled(product_id))

        # Cleanup test.
        profile_registry.unregisterProfile('default', product_id)

    def testCleanupUninstalledProducts(self):
        from plone.app.upgrade.v43.final import cleanupUninstalledProducts
        qi = getToolByName(self.portal, 'portal_quickinstaller', None)
        if qi is None:
            # Newer Plone without qi.
            return
        setup = getToolByName(self.portal, 'portal_setup')
        # Register three profiles.  I wanted to take 'new' as product
        # id, but there is already a python module 'new', so that goes
        # wrong.
        profile_registry.registerProfile(
            'default', '', '', '/my/path',
            product='newproduct', profile_type=EXTENSION)
        profile_registry.registerProfile(
            'default', '', '', '/my/path',
            product='installed', profile_type=EXTENSION)
        profile_registry.registerProfile(
            'default', '', '', '/my/path',
            product='uninstalled', profile_type=EXTENSION)
        # Mark as installed.
        setup.setLastVersionForProfile('newproduct:default', '1')
        setup.setLastVersionForProfile('installed:default', '1')
        setup.setLastVersionForProfile('uninstalled:default', '1')
        # Notify of installation of three products.
        qi.notifyInstalled('newproduct', status='new')
        qi.notifyInstalled('installed', status='installed')
        qi.notifyInstalled('uninstalled', status='uninstalled')
        # The status differs, so QI does not think all are actually
        # installed.
        self.assertFalse(qi.isProductInstalled('newproduct'))
        self.assertTrue(qi.isProductInstalled('installed'))
        self.assertFalse(qi.isProductInstalled('uninstalled'))
        # But all three have an object in the QI.
        self.assertTrue('newproduct' in qi)
        self.assertTrue('installed' in qi)
        self.assertTrue('uninstalled' in qi)
        # And all three have a version in GS.
        self.assertEqual(
            setup.getLastVersionForProfile('newproduct:default'), ('1',))
        self.assertEqual(
            setup.getLastVersionForProfile('installed:default'), ('1',))
        self.assertEqual(
            setup.getLastVersionForProfile('uninstalled:default'), ('1',))
        # Call our cleanup function.
        cleanupUninstalledProducts(setup)
        # Same results for isProductInstalled.
        self.assertFalse(qi.isProductInstalled('newproduct'))
        self.assertTrue(qi.isProductInstalled('installed'))
        self.assertFalse(qi.isProductInstalled('uninstalled'))
        # The two not installed items are removed.
        self.assertFalse('newproduct' in qi)
        self.assertTrue('installed' in qi)
        self.assertFalse('uninstalled' in qi)
        # Those twee are unknown in GS.
        self.assertEqual(
            setup.getLastVersionForProfile('newproduct:default'), 'unknown')
        self.assertEqual(
            setup.getLastVersionForProfile('installed:default'), ('1',))
        self.assertEqual(
            setup.getLastVersionForProfile('uninstalled:default'), 'unknown')
        # Cleanup test.
        profile_registry.unregisterProfile('default', 'newproduct')
        profile_registry.unregisterProfile('default', 'installed')
        profile_registry.unregisterProfile('default', 'uninstalled')


if not six.PY2:
    def test_suite():
        return unittest.TestSuite()
