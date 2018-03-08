import pkg_resources
import sys
from plone.app.upgrade.utils import alias_module
import bbb
import bbbd

try:
    from zope.app.cache.interfaces.ram import IRAMCache
except ImportError:
    import zope.ramcache.interfaces.ram
    alias_module('zope.app.cache.interfaces.ram', zope.ramcache.interfaces.ram)
    import zope.ramcache.ram
    alias_module('zope.app.cache.ram', zope.ramcache.ram)

if 'products.kupu' not in pkg_resources.working_set.by_key:
    import kupu_bbb
    alias_module('Products.kupu.plone.plonelibrarytool', kupu_bbb)

try:
    from Products.CMFCalendar import interfaces
except ImportError:
    alias_module('Products.CMFCalendar.interfaces', bbb)

try:
    from Products.CMFPlone import CalendarTool
except ImportError:
    sys.modules['Products.CMFPlone.CalendarTool'] = bbb

try:
    from Products.CMFPlone import DiscussionTool
except ImportError:
    sys.modules['Products.CMFPlone.DiscussionTool'] = bbb

try:
    from Products.CMFPlone import InterfaceTool
except ImportError:
    sys.modules['Products.CMFPlone.InterfaceTool'] = bbb

try:
    from Products.CMFPlone import SyndicationTool
except ImportError:
    sys.modules['Products.CMFPlone.SyndicationTool'] = bbb

try:
    from Products.CMFPlone import UndoTool
except ImportError:
    sys.modules['Products.CMFPlone.UndoTool'] = bbb


try:
    import Products.TinyMCE
except ImportError:
    alias_module('Products.TinyMCE.utility', bbb)
    alias_module('Products.TinyMCE.interfaces.utility', bbb)


try:
    import Products.CMFActionIcons
except ImportError:
    alias_module('Products.CMFPlone.ActionIconsTool', bbb)
    alias_module('Products.CMFActionIcons.interfaces', bbb)
    alias_module('Products.CMFActionIcons.interfaces._tools', bbb)
    alias_module('Products.CMFActionIcons.ActionIconsTool', bbb)

try:
    import Products.CMFPlone.FactoryTool
except ImportError:
    try:
        pkg_resources.get_distribution('Products.ATContentTypes')
    except:
        from plone.app.upgrade import atcontentypes_bbb
        alias_module('Products.CMFPlone.FactoryTool', atcontentypes_bbb)
    else:
        from Products.ATContentTypes.tool import factory
        alias_module('Products.CMFPlone.FactoryTool', factory)

try:
    import Products.CMFPlone.MetadataTool
    Products.CMFPlone.MetadataTool  # pyflakes
except ImportError:
    try:
        pkg_resources.get_distribution('Products.ATContentTypes')
    except:
        from plone.app.upgrade import atcontentypes_bbb
        alias_module('Products.CMFPlone.MetadataTool', atcontentypes_bbb)
    else:
        from Products.ATContentTypes.tool import metadata
        alias_module('Products.CMFPlone.MetadataTool', metadata)

try:
    import Products.CMFDefault.MetadataTool
    Products.CMFDefault.MetadataTool  # pyflakes
except ImportError:
    try:
        pkg_resources.get_distribution('Products.ATContentTypes')
    except:
        from plone.app.upgrade import atcontentypes_bbb
        alias_module('Products.CMFDefault.MetadataTool', atcontentypes_bbb)
    else:
        from Products.ATContentTypes.tool import metadata
        sys.modules['Products.CMFDefault.MetadataTool'] = metadata

try:
    import Products.CMFDefault.SyndicationInfo
    Products.CMFDefault.SyndicationInfo  # pyflakes
except ImportError:
    sys.modules['Products.CMFDefault.SyndicationInfo'] = bbb

try:
    from Products.PloneLanguageTool import interfaces
except ImportError:
    alias_module('Products.PloneLanguageTool.interfaces', bbb)
    alias_module('Products.PloneLanguageTool', bbbd)
    __import__('Products.PloneLanguageTool.LanguageTool').PloneLanguageTool.LanguageTool = __import__(
        'Products.PloneLanguageTool.LanguageTool').PloneLanguageTool.LanguageTool.LanguageTool


# To solve the __iro__ problem because CMFPlacefulWorkflow interfaces
# changed on 1.6.1
try:
    pkg_resources.get_distribution('Products.CMFPlacefulWorkflow')
    from Products.CMFPlacefulWorkflow.interfaces import portal_placeful_workflow
except pkg_resources.DistributionNotFound:
    # No package in this environment requires CMFPlacefulWorkflow,
    # so no patching necessary
    pass
except:
    from Products.CMFPlacefulWorkflow import interfaces
    alias_module(
        'Products.CMFPlacefulWorkflow.interfaces.portal_placeful_workflow', interfaces)

try:
    from Products.PasswordResetTool import PasswordResetTool
    PasswordResetTool  # pyflakes
except ImportError:
    sys.modules['Products.PasswordResetTool.PasswordResetTool'] = bbb


class HiddenProducts(object):
    """This hides the upgrade profiles from the quick installer tool."""

    def getNonInstallableProducts(self):
        return [
            'plone.app.upgrade.v40',
            'plone.app.upgrade.v41',
            'plone.app.upgrade.v42',
            'plone.app.upgrade.v43',
            'plone.app.upgrade.v50',
            'plone.app.upgrade.v51',
            'plone.app.upgrade.v52',
        ]

    def getNonInstallableProfiles(self):
        return []
