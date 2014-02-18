from zope.component import getUtility
from zope.component import getSiteManager
from zope.component import getMultiAdapter
from plone.portlets.interfaces import IPortletManager
from Products.CMFCore.utils import getToolByName
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.app.viewletmanager.interfaces import IViewletSettingsStorage


from plone.app.upgrade.tests.base import MigrationTest

import alphas


class PASUpgradeTest(MigrationTest):

    def test_double_upgrade(self):
        # Check that calling our upgrade twice does no harm.
        alphas.lowercase_email_login(self.portal)
        alphas.lowercase_email_login(self.portal)

    def test_upgrade_with_email_login(self):
        pas = getToolByName(self.portal, 'acl_users')
        regtool = getToolByName(self.portal, 'portal_registration')
        regtool.addMember('JOE', 'somepassword')
        self.assertEqual(pas.getUserById('JOE').getUserName(), 'JOE')

        # First call.
        alphas.lowercase_email_login(self.portal)
        self.assertEqual(pas.getProperty('login_transform'), '')
        self.assertEqual(pas.getUserById('JOE').getUserName(), 'JOE')

        # If email as login is enabled, we want to use lowercase login
        # names, even when that login name is not an email address.
        ptool = getToolByName(self.portal, 'portal_properties')
        ptool.site_properties.manage_changeProperties(use_email_as_login=True)

        # Second call.
        alphas.lowercase_email_login(self.portal)
        self.assertEqual(pas.getProperty('login_transform'), 'lower')
        self.assertEqual(pas.getUserById('JOE').getUserName(), 'joe')

    def test_footer_portletmanager_added(self):
        sm = getSiteManager(self.portal)
        registrations = [r.name for r in sm.registeredUtilities()
                         if IPortletManager == r.provided]
        self.assertTrue('plone.footerportlets' in registrations)
        manager = getUtility(IPortletManager, name='plone.footerportlets', context=self.portal)
        mapping = getMultiAdapter((self.portal, manager), IPortletAssignmentMapping)
        self.assertEqual(['footer', 'actions', 'colophon'], mapping.keys())

    def test_footer_viewlets_hidden(self):

        storage = getUtility(IViewletSettingsStorage)
        manager = "plone.portalfooter"
        skinname = self.portal.getCurrentSkinName()

        hidden_viewlets = storage.getHidden(manager, skinname)

        self.assertEqual((u'plone.colophon', u'plone.site_actions'),
                         hidden_viewlets)


def test_suite():
    from unittest import TestSuite, makeSuite
    try:
        from Products.CMFPlone.factory import _IMREALLYPLONE5
    except ImportError:
        return TestSuite()
    else:
        suite = TestSuite()
        suite.addTest(makeSuite(PASUpgradeTest))
        return suite
