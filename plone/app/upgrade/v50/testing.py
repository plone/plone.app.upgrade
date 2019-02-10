# -*- coding: utf-8 -*-
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.utils import plone_version
from plone.testing.z2 import FunctionalTesting
from plone.testing.z2 import login
from zope.component.hooks import setSite

import logging
import os


logger = logging.getLogger(__file__)


class RealUpgradeLayer(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # load ZCML
        # In 5.0 alpha we install or upgrade plone.app.caching,
        # so it must be available to Zope..
        import plone.app.caching
        self.loadZCML(
            name='configure.zcml',
            package=plone.app.caching,
        )

    def setUpPloneSite(self, portal):
        app = portal.aq_parent
        login(app['acl_users'], 'admin')
        # import old ZEXP
        try:
            path = os.path.join(os.path.abspath(
                os.path.dirname(__file__)), 'data', 'test-full.zexp')
            app._importObjectFromFile(path, verify=0)
        except Exception:
            logger.exception('Failed to import ZEXP from old site.')
        else:
            # run upgrades
            self['portal'] = portal = app.test
            setSite(portal)
            if plone_version >= '5.2':
                # for 5.2 we need tools as utilities
                loadMigrationProfile(
                    portal.portal_setup,
                    'profile-plone.app.upgrade.v52:to52alpha1',
                    steps=['componentregistry'])
            portal.portal_migration.upgrade(swallow_errors=False)
            setSite(None)

    def tearDownPloneSite(self, portal):
        try:
            del self['portal']
        except KeyError:
            pass


REAL_UPGRADE_FIXTURE = RealUpgradeLayer()
REAL_UPGRADE_FUNCTIONAL = FunctionalTesting(
    bases=(REAL_UPGRADE_FIXTURE,), name='plone.app.upgrade:4.0 -> 5.0')
