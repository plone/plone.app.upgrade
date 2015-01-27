from borg.localrole.utils import replace_local_role_manager
from zope.interface import noLongerProvides

from Products.PlonePAS.interfaces.plugins import ILocalRolesPlugin

from plone.app.upgrade.tests.base import FunctionalUpgradeTestCase
from plone.app.upgrade.tests.base import MigrationTest
from plone.app.upgrade.utils import version_match

from plone.app.upgrade.v31.betas import reinstallCMFPlacefulWorkflow


class TestMigrations_v3_1(MigrationTest):

    def afterSetUp(self):
        self.qi = self.portal.portal_quickinstaller
        self.wf = self.portal.portal_workflow
        self.ps = self.portal.portal_setup

    def testReinstallCMFPlacefulWorkflow(self):
        try:
            from Products.CMFPlacefulWorkflow.interfaces import IPlacefulMarker
        except ImportError:
            return
        # first the product needs to be installed
        self.qi.installProduct('CMFPlacefulWorkflow')
        # Delete existing logs to prevent race condition
        self.ps.manage_delObjects(self.ps.objectIds())
        # We remove the new marker, to ensure it's added on reinstall
        if IPlacefulMarker.providedBy(self.wf):
            noLongerProvides(self.wf, IPlacefulMarker)
        reinstallCMFPlacefulWorkflow(self.portal, [])
        self.assertTrue(IPlacefulMarker.providedBy(self.wf))

    def testReinstallCMFPlacefulWorkflowDoesNotInstall(self):
        reinstallCMFPlacefulWorkflow(self.portal, [])
        self.assertFalse(self.qi.isProductInstalled('CMFPlacefulWorkflow'))

    def testReinstallCMFPlacefulWorkflowNoTool(self):
        self.portal._delObject('portal_quickinstaller')
        reinstallCMFPlacefulWorkflow(self.portal, [])

    def testReplaceLocalRoleManager(self):
        # first we replace the local role manager with the one from PlonePAS
        uf = self.portal.acl_users
        # deactivate and remove the borg plugin
        uf.plugins.removePluginById('borg_localroles')
        uf.manage_delObjects(['borg_localroles'])
        # activate the standard plugin
        uf.plugins.activatePlugin(ILocalRolesPlugin, 'local_roles')
        # Bring things back to normal
        replace_local_role_manager(self.portal)
        plugins = uf.plugins.listPlugins(ILocalRolesPlugin)
        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0][0], 'borg_localroles')

    def testReplaceLocalRoleManagerTwice(self):
        # first we replace the local role manager with the one from PlonePAS
        uf = self.portal.acl_users
        # deactivate and remove the borg plugin
        uf.plugins.removePluginById('borg_localroles')
        uf.manage_delObjects(['borg_localroles'])
        # activate the standard plugin
        uf.plugins.activatePlugin(ILocalRolesPlugin, 'local_roles')
        # run the upgrade twice
        replace_local_role_manager(self.portal)
        replace_local_role_manager(self.portal)
        plugins = uf.plugins.listPlugins(ILocalRolesPlugin)
        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0][0], 'borg_localroles')

    def testReplaceLocalRoleManagerNoPlugin(self):
        # first we replace the local role manager with the one from PlonePAS
        uf = self.portal.acl_users
        # deactivate and remove the borg plugin
        uf.plugins.removePluginById('borg_localroles')
        uf.manage_delObjects(['borg_localroles'])
        # delete the standard plugin
        uf.manage_delObjects(['local_roles'])
        # Run the upgrade, which shouldn't fail even if the expected
        # plugin is missing
        replace_local_role_manager(self.portal)
        plugins = uf.plugins.listPlugins(ILocalRolesPlugin)
        self.assertEqual(len(plugins), 1)
        self.assertEqual(plugins[0][0], 'borg_localroles')

    def testReplaceLocalRoleManagerNoPAS(self):
        uf = self.portal.acl_users
        # delete the plugin registry
        uf._delObject('plugins')
        replace_local_role_manager(self.portal)

    def testReplaceLocalRoleManagerNoUF(self):
        # Delete the user folder
        replace_local_role_manager(self.portal)

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


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    if not version_match('3.1'):
        return suite
    suite.addTest(makeSuite(TestMigrations_v3_1))
    suite.addTest(makeSuite(TestFunctionalMigrations))
    return suite
