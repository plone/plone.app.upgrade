# -*- coding: utf-8 -*-
from os.path import abspath
from os.path import dirname
from os.path import join
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import FunctionalTesting
from plone.app.testing.bbb import PTC_FIXTURE
from plone.app.testing.bbb import PloneTestCase
from Products.CMFCore.interfaces import IActionCategory
from Products.CMFCore.interfaces import IActionInfo
from Products.CMFCore.tests.base.testcase import WarningInterceptor
from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.context import TarballImportContext
from zope.configuration import xmlconfig
from zope.site.hooks import setSite

import transaction

#
# Base TestCase for upgrades
#


class UpgradeTestCaseFixture(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # In 5.0 alpha we install or upgrade plone.app.caching,
        # so it must be available to Zope.
        import plone.app.caching
        xmlconfig.file(
            'configure.zcml',
            plone.app.caching,
            context=configurationContext
        )


UPGRADE_TEST_CASE_FIXTURE = UpgradeTestCaseFixture()
UPGRADE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(PTC_FIXTURE, UPGRADE_TEST_CASE_FIXTURE),
    name='UpgradeTestCase:Functional')


class MigrationTest(PloneTestCase):

    layer = UPGRADE_FUNCTIONAL_TESTING

    def removeActionFromTool(
        self,
        action_id,
        category=None,
        action_provider='portal_actions'
    ):
        # Removes an action from portal_actions
        tool = getToolByName(self.portal, action_provider)
        if category is None:
            if action_id in tool.objectIds() and \
               IActionInfo.providedBy(tool._getOb(action_id)):
                tool._delOb(action_id)
        elif (
            category in tool.objectIds() and
            IActionCategory.providedBy(tool._getOb(category)) and
            action_id in tool.objectIds() and
            IActionInfo.providedBy(tool._getOb(action_id))
        ):
            tool._delOb(action_id)

    def addResourceToJSTool(self, resource_name):
        # Registers a resource with the javascripts tool
        tool = getToolByName(self.portal, 'portal_javascripts')
        if resource_name not in tool.getResourceIds():
            tool.registerScript(resource_name)

    def addResourceToCSSTool(self, resource_name):
        # Registers a resource with the css tool
        tool = getToolByName(self.portal, 'portal_css')
        if resource_name not in tool.getResourceIds():
            tool.registerStylesheet(resource_name)

    def removeSiteProperty(self, property_id):
        # Removes a site property from portal_properties
        tool = getToolByName(self.portal, 'portal_properties')
        sheet = getattr(tool, 'site_properties')
        if sheet.hasProperty(property_id):
            sheet.manage_delProperties([property_id])

    def addSiteProperty(self, property_id):
        # adds a site property to portal_properties
        tool = getToolByName(self.portal, 'portal_properties')
        sheet = getattr(tool, 'site_properties')
        if not sheet.hasProperty(property_id):
            sheet.manage_addProperty(property_id, [], 'lines')

    def removeNavTreeProperty(self, property_id):
        # Removes a navtree property from portal_properties
        tool = getToolByName(self.portal, 'portal_properties')
        sheet = getattr(tool, 'navtree_properties')
        if sheet.hasProperty(property_id):
            sheet.manage_delProperties([property_id])

    def addNavTreeProperty(self, property_id):
        # adds a navtree property to portal_properties
        tool = getToolByName(self.portal, 'portal_properties')
        sheet = getattr(tool, 'navtree_properties')
        if not sheet.hasProperty(property_id):
            sheet.manage_addProperty(property_id, [], 'lines')

    def removeMemberdataProperty(self, property_id):
        # Removes a memberdata property from portal_memberdata
        tool = getToolByName(self.portal, 'portal_memberdata')
        if tool.hasProperty(property_id):
            tool.manage_delProperties([property_id])

    def uninstallProduct(self, product_name):
        # Removes a product
        try:
            from Products.CMFPlone.utils import get_installer
        except ImportError:
            # BBB For Plone 5.0 and lower.
            qi = getToolByName(self.portal, 'portal_quickinstaller', None)
            if qi is None:
                return
        else:
            qi = get_installer(self.portal)
        if qi.isProductInstalled(product_name):
            qi.uninstallProducts([product_name])

    def addSkinLayer(self, layer, skin='Plone Default', pos=None):
        # Adds a skin layer at pos. If pos is None, the layer is appended
        skins = getToolByName(self.portal, 'portal_skins')
        path = skins.getSkinPath(skin)
        path = [x.strip() for x in path.split(',')]
        if layer in path:
            path.remove(layer)
        if pos is None:
            path.append(layer)
        else:
            path.insert(pos, layer)
        skins.addSkinSelection(skin, ','.join(path))

    def removeSkinLayer(self, layer, skin='Plone Default'):
        # Removes a skin layer from skin
        skins = getToolByName(self.portal, 'portal_skins')
        path = skins.getSkinPath(skin)
        path = [x.strip() for x in path.split(',')]
        if layer in path:
            path.remove(layer)
            skins.addSkinSelection(skin, ','.join(path))


class FunctionalUpgradeTestCase(PloneTestCase, WarningInterceptor):

    _setup_fixture = 0
    site_id = 'test'

    def afterSetUp(self):
        self.loginAsPortalOwner()
        setSite(self.portal)
        setSite(None)

    def beforeTearDown(self):
        if self.site_id in self.app:
            self.app._delObject(self.site_id)
        self.logout()
        transaction.commit()

    def importFile(self, context, name):
        path = join(abspath(dirname(context)), 'data', name)
        self._trap_warning_output()
        self.app._importObjectFromFile(path, verify=0)
        self._free_warning_output()

    def migrate(self):
        oldsite = getattr(self.app, self.site_id)
        mig = oldsite.portal_migration
        components = getattr(oldsite, '_components', None)
        if components is not None:
            setSite(oldsite)
        result = mig.upgrade(swallow_errors=False)
        return (oldsite, result)

    def export(self):
        oldsite = getattr(self.app, self.site_id)
        setSite(oldsite)
        stool = oldsite.portal_setup
        upgraded_export = stool.runAllExportSteps()

        upgraded = TarballImportContext(stool, upgraded_export['tarball'])
        return stool.compareConfigurations(upgraded, self.expected)
