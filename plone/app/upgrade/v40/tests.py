from Products.CMFCore.ActionInformation import Action
from Products.CMFCore.utils import getToolByName

from plone.app.upgrade.utils import loadMigrationProfile
from plone.app.upgrade.tests.base import MigrationTest

from plone.app.upgrade.v40.alphas import _KNOWN_ACTION_ICONS
from plone.app.upgrade.v40.alphas import migrateActionIcons


class TestMigrations_v4_0alpha1(MigrationTest):

    profile = "profile-plone.app.upgrade:3-4alpha1"

    def afterSetUp(self):
        self.atool = getToolByName(self.portal, 'portal_actions')
        self.aitool = getToolByName(self.portal, 'portal_actionicons')

    def testProfile(self):
        # This tests the whole migration profile can be loaded
        loadMigrationProfile(self.portal, self.profile)
        self.failUnless(True)

    def testMigrateActionIcons(self):
        _KNOWN_ACTION_ICONS['object_buttons'].extend(['test_id', 'test2_id'])
        self.aitool.addActionIcon(
            category='object_buttons',
            action_id='test_id',
            icon_expr='test.gif',
            title='Test my icon',
            )
        self.aitool.addActionIcon(
            category='object_buttons',
            action_id='test2_id',
            icon_expr='python:context.getIcon()',
            title='Test my second icon',
            )
        test_action = Action('test_id',
            title='Test me',
            description='',
            url_expr='',
            icon_expr='',
            available_expr='',
            permissions=('View', ),
            visible = True)
        test2_action = Action('test2_id',
            title='Test me too',
            description='',
            url_expr='',
            icon_expr='',
            available_expr='',
            permissions=('View', ),
            visible = True)

        object_buttons = self.atool.object_buttons
        if getattr(object_buttons, 'test_id', None) is None:
            object_buttons._setObject('test_id', test_action)
        if getattr(object_buttons, 'test2_id', None) is None:
            object_buttons._setObject('test2_id', test2_action)

        self.assertEqual(object_buttons.test_id.icon_expr, '')
        self.assertEqual(object_buttons.test2_id.icon_expr, '')
        self.assertEqual(self.aitool.getActionIcon('object_buttons', 'test_id'),
                        'test.gif')
        # Test it twice
        for i in range(2):
            migrateActionIcons(self.portal)
            icons = [ic.getActionId() for ic in self.aitool.listActionIcons()]
            self.failIf('test_id' in icons)
            self.failIf('test2_id' in icons)
            self.assertEqual(object_buttons.test_id.icon_expr,
                             'string:$portal_url/test.gif')
            self.assertEqual(object_buttons.test2_id.icon_expr,
                             'python:context.getIcon()')

    def testPngContentIcons(self):
        tt = getToolByName(self.portal, "portal_types")
        tt.Document.content_icon = "document_icon.gif"
        loadMigrationProfile(self.portal, self.profile, ('typeinfo', ))
        self.assertEqual(tt.Document.content_icon, "document_icon.png")


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestMigrations_v4_0alpha1))
    return suite
