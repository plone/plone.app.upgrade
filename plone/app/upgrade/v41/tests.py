from plone.app.upgrade.tests.base import MigrationTest


class TestMigrations_v4_1alpha1(MigrationTest):
    pass


def test_suite():
    from unittest import defaultTestLoader
    return defaultTestLoader.loadTestsFromName(__name__)
