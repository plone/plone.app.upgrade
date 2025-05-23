from plone.app.upgrade import utils
from plone.app.upgrade.tests.base import MigrationTest
from Products.CMFCore.utils import getToolByName


class TestUtils(MigrationTest):
    def testCleanUpSkinsTool(self):
        # This removes no longer existing layers from the skins tool and the
        # skin selections.
        from Products.CMFCore.DirectoryView import DirectoryView
        from Products.CMFCore.DirectoryView import registerDirectory

        self.setRoles(["Manager"])
        skins = getToolByName(self.portal, "portal_skins")
        existing = skins.keys()
        selection = "Plone Default"

        def layers_in_selection(selection_name):
            return skins.getSkinPath(selection_name).split(",")

        existing_layers_in_selection = layers_in_selection(selection)

        # An initial cleanup should do nothing.
        utils.cleanUpSkinsTool(self.portal)
        difference = set(existing) ^ set(skins)
        self.assertEqual(
            len(skins.keys()),
            len(existing),
            msg=f"Skink difference is: {list(difference)}",
        )
        difference = set(layers_in_selection(selection)) ^ set(
            existing_layers_in_selection
        )
        self.assertEqual(
            len(layers_in_selection(selection)),
            len(existing_layers_in_selection),
            msg=f"Layer difference is: {list(difference)}",
        )

        # A second cleanup should also do nothing.  We used to rename
        # plone_styles to classic_styles on the first run, which would get
        # removed on a second run because in these tests the class_styles layer
        # is not available.
        utils.cleanUpSkinsTool(self.portal)
        self.assertEqual(len(skins.keys()), len(existing))
        self.assertEqual(
            len(layers_in_selection(selection)), len(existing_layers_in_selection)
        )

        # Register some test skins layers.  Note: the current module name is
        # taken from globals()['__name__'], which is how registerDirectory
        # knows where to find the directory.  Also note that you should not try
        # to register any layer that is outside of the current directory or in
        # a 'skins' sub directory.  There is just too much crazyness in the
        # api.  Better try to load some zcml in that case.
        skin_name = "skin_test"
        # Make it available for Zope.  This is what you would do in zcml.
        registerDirectory(skin_name, globals(), subdirs=1)
        # Add the DirectoryView object to portal_skins.
        directory_info = DirectoryView(
            skin_name, reg_key=f"plone.app.upgrade.tests:{skin_name}"
        )
        skins._setObject(skin_name, directory_info)

        # Add its sub skins to a skin selection.
        self.addSkinLayer("skin_test/sub1", skin=selection)
        self.addSkinLayer("skin_test/sub1/subsub1", skin=selection)
        self.addSkinLayer("skin_test/sub2", skin=selection)

        # Did that work?
        self.assertEqual(len(skins.keys()), len(existing) + 1)
        self.assertEqual(
            len(layers_in_selection(selection)), len(existing_layers_in_selection) + 3
        )

        # Clean it up again.  Nothing should be removed.
        utils.cleanUpSkinsTool(self.portal)
        self.assertEqual(len(skins.keys()), len(existing) + 1)
        self.assertEqual(
            len(layers_in_selection(selection)), len(existing_layers_in_selection) + 3
        )


def test_suite():
    import unittest

    return unittest.TestSuite(
        (unittest.defaultTestLoader.loadTestsFromTestCase(TestUtils),)
    )
