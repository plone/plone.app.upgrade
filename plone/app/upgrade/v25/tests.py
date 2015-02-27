from Products.CMFPlone.UnicodeSplitter import Splitter
from Products.CMFPlone.UnicodeSplitter import CaseNormalizer

from plone.app.upgrade.tests.base import FunctionalUpgradeTestCase
from plone.app.upgrade.tests.base import MigrationTest
from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.utils import version_match

from plone.app.upgrade.v25 import fixupPloneLexicon
from plone.app.upgrade.v25 import setLoginFormInCookieAuth
from plone.app.upgrade.v25 import addMissingMimeTypes


class TestMigrations_v2_5_0(MigrationTest):

    def afterSetUp(self):
        self.profile = 'profile-plone.app.upgrade.v25:2.5final-2.5.1'
        self.actions = self.portal.portal_actions
        self.css = self.portal.portal_css

    def tesFixObjDeleteAction(self):
        # Prepare delete actions test
        editActions = ('delete',)
        for a in editActions:
            self.removeActionFromTool(a, category='object_buttons')
        loadMigrationProfile(self.portal, self.profile, ('actions', ))
        # delete action tests
        actions = [x.id for x in self.actions.object_buttons.listActions()
                   if x.id in editActions]
        # check that all of our deleted actions are now present
        for a in editActions:
            self.assertTrue(a in actions)
        # ensure that they are present only once
        self.assertEqual(len(editActions), len(actions))

    def testFixupPloneLexicon(self):
        # Should update the plone_lexicon pipeline
        lexicon = self.portal.portal_catalog.plone_lexicon
        lexicon._pipeline = (object(), object())
        # Test it twice
        for i in range(2):
            fixupPloneLexicon(self.portal)
            self.assertTrue(isinstance(lexicon._pipeline[0], Splitter))
            self.assertTrue(isinstance(lexicon._pipeline[1], CaseNormalizer))


class TestMigrations_v2_5_1(MigrationTest):

    def afterSetUp(self):
        self.actions = self.portal.portal_actions
        self.memberdata = self.portal.portal_memberdata
        self.catalog = self.portal.portal_catalog
        self.skins = self.portal.portal_skins
        self.types = self.portal.portal_types
        self.workflow = self.portal.portal_workflow
        self.css = self.portal.portal_css

    def testSetLoginFormInCookieAuth(self):
        setLoginFormInCookieAuth(self.portal)
        cookie_auth = self.portal.acl_users.credentials_cookie_auth
        self.assertEqual(cookie_auth.getProperty('login_path'),
                             'require_login')

    def testSetLoginFormNoCookieAuth(self):
        # Shouldn't error
        uf = self.portal.acl_users
        uf._delOb('credentials_cookie_auth')
        setLoginFormInCookieAuth(self.portal)

    def testSetLoginFormAlreadyChanged(self):
        # Shouldn't change the value if it's not the default
        cookie_auth = self.portal.acl_users.credentials_cookie_auth
        cookie_auth.manage_changeProperties(login_path='foo')
        setLoginFormInCookieAuth(self.portal)
        self.assertTrue(cookie_auth.getProperty('login_path') != 'require_login')

class TestMigrations_v2_5_2(MigrationTest):

    def afterSetUp(self):
        self.mimetypes = self.portal.mimetypes_registry

    def testMissingMimeTypes(self):
        # we're testing for 'text/x-web-markdown' and 'text/x-web-textile'
        missing_types = ['text/x-web-markdown', 'text/x-web-textile']
        # since we're running a full 2.5.4 instance in this test, the missing
        # types might in fact already be there:
        current_types = self.mimetypes.list_mimetypes()
        types_to_delete = []
        for mtype in missing_types:
            if mtype in current_types:
                types_to_delete.append(mtype)
        if types_to_delete:
            self.mimetypes.manage_delObjects(types_to_delete)
        # now they're gone:
        self.assertFalse(set(self.mimetypes.list_mimetypes()).issuperset(set(missing_types)))
        addMissingMimeTypes(self.portal)
        # now they're back:
        self.assertTrue(set(self.mimetypes.list_mimetypes()).issuperset(set(missing_types)))


class TestFunctionalMigrations(FunctionalUpgradeTestCase):

    def testUpgrade(self):
        self.importFile(__file__, 'test-base.zexp')
        oldsite, result = self.migrate()

        mig = oldsite.portal_migration
        self.assertFalse(mig.needUpgrading())

    def testDCMIStorageUpdated(self):
        self.importFile(__file__, 'test-base.zexp')
        oldsite, result = self.migrate()

        dcmi = getattr(oldsite.portal_metadata, 'DCMI', None)
        self.assertFalse(dcmi is None)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    if not version_match('2.5'):
        return suite
    suite.addTest(makeSuite(TestMigrations_v2_5_0))
    suite.addTest(makeSuite(TestMigrations_v2_5_1))
    suite.addTest(makeSuite(TestMigrations_v2_5_2))
    suite.addTest(makeSuite(TestFunctionalMigrations))
    return suite
