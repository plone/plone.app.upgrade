# -*- coding: utf-8 -*-
from OFS.SimpleItem import SimpleItem
from ZPublisher import BeforeTraverse


class LanguageTool(SimpleItem):

    def __call__(self, container, req):
        pass

    def manage_beforeDelete(self, item, container):
        if item is self:
            handle = self.meta_type + '/' + self.getId()
            BeforeTraverse.unregisterBeforeTraverse(container, handle)
