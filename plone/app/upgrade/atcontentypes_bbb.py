from OFS.SimpleItem import SimpleItem
from Products.CMFCore.utils import registerToolInterface
from zope.interface import Interface


MetadataTool = SimpleItem


class FactoryTool(SimpleItem):
    ''' Compatibility code for portal_factory
    '''
    def __nonzero__(self):
        ''' Always evealuate to False
        '''
        return 0


class IFactoryTool(Interface):
    pass
registerToolInterface('portal_factory', IFactoryTool)
