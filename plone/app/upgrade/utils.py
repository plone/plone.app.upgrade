import logging

from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.interfaces import ISetupTool

_marker = []

logger = logging.getLogger('plone.app.upgrade')


def null_upgrade_step(tool):
    """ This is a null migration, use it when nothing happens """
    pass

def loadMigrationProfile(context, profile, steps=_marker):
    if not ISetupTool.providedBy(context):
        context = getToolByName(context, "portal_setup")
    if steps is _marker:
        context.runAllImportStepsFromProfile(profile, purge_old=False)
    else:
        for step in steps:
            context.runImportStepFromProfile(profile,
                                             step,
                                             run_dependencies=False,
                                             purge_old=False)
