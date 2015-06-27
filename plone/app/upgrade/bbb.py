from OFS.SimpleItem import SimpleItem
from Products.CMFCore.utils import registerToolInterface
from zope.interface import Interface
from ZPublisher import BeforeTraverse


CalendarTool = SimpleItem
DiscussionTool = SimpleItem
InterfaceTool = SimpleItem
SyndicationTool = SimpleItem
UndoTool = SimpleItem
TinyMCE = SimpleItem


class ILanguageTool(Interface):
    pass


class ITinyMCE(Interface):
    pass


class ICalendarTool(Interface):
    pass


class IActionIconsTool(Interface):
    pass
registerToolInterface('portal_actionicons', IActionIconsTool)


class ActionIcon(SimpleItem):

    _title = None
    _category = 'object'
    _action_id = 'view'
    _icon_expr_text = 'document_icon'

    def __init__(self, category, action_id, icon_expr_text='', title=None):
        self._category = category
        self._action_id = action_id
        self._icon_expr_text = icon_expr_text
        self._title = title


class ActionIconsTool(SimpleItem):

    def __init__(self):
        self._icons = ()
        self._lookup = {}

    def listActionIcons(self):
        return [x.__of__(self) for x in self._icons]

    def addActionIcon(self, category, action_id, icon_expr, title=None):
        icons = list(self._icons)
        icons.append(ActionIcon(category, action_id, icon_expr, title))
        self._lookup[(category, action_id)] = icons[-1]
        self._icons = tuple(icons)

    def removeActionIcon(self, category, action_id):
        icons = list(self._icons)
        icon = self._lookup[(category, action_id)]
        icons.remove(icon)
        del self._lookup[(category, action_id)]
        self._icons = tuple(icons)

# BBB from CMFDefault
class SyndicationInformation(SimpleItem):
        id='syndication_information'
        meta_type='SyndicationInformation'
