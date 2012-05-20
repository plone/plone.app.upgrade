from OFS import SimpleItem


class PloneKupuLibraryTool(SimpleItem.SimpleItem):

    def get_stripped_attributes(self):
        stripped = []
        for (tags, attrs) in self.getHtmlExclusions():
            if not tags:
                stripped.extend(attrs)
        return stripped

    def get_stripped_combinations(self):
        stripped = [(tags, attrs) for (tags, attrs) in
            self.getHtmlExclusions() if tags and attrs]
        return stripped

    def getHtmlExclusions(self):
        excl = getattr(self, 'html_exclusions', ())
        res = []
        for (t, a) in excl:
            if t and t[0] == '':
                t = []
            if a and a[0] == '':
                a = []
            res.append((t, a))
        return res
