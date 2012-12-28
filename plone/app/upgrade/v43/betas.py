from Products.CMFCore.utils import getToolByName

def upgradeNewsItemToBlob(context):
    qi = getToolByName(context, 'portal_quickinstaller')
    qi.upgradeProduct('plone.app.blob')
