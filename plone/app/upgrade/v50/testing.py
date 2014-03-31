from plone.app.testing import PloneSandboxLayer
from plone.app.testing import PLONE_FIXTURE
from plone.testing.z2 import FunctionalTesting, login
from zope.component.hooks import setSite
import os


class RealUpgradeLayer(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE,)

    def setUpPloneSite(self, portal):
        app = portal.aq_parent
        login(app['acl_users'], 'admin')

        # import old ZEXP
        path = os.path.join(os.path.abspath(
            os.path.dirname(__file__)), 'data', 'test-full.zexp')
        app._importObjectFromFile(path, verify=0)

        # run upgrades
        self['portal'] = portal = app.test
        setSite(portal)
        portal.portal_migration.upgrade(swallow_errors=False)
        setSite(None)

    def tearDownPloneSite(self, portal):
        del self['portal']


REAL_UPGRADE_FIXTURE = RealUpgradeLayer()
REAL_UPGRADE_FUNCTIONAL = FunctionalTesting(
    bases=(REAL_UPGRADE_FIXTURE,), name='plone.app.upgrade:4.0 -> 5.0')
