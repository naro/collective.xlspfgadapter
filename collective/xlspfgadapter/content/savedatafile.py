""" File input saved as content. This is a special content type due to security requirements """

from Products.ATContentTypes.content.base import registerATCT
from Products.CMFCore.permissions import ModifyPortalContent
from Products.ATContentTypes.content.file import ATFile
from AccessControl import ClassSecurityInfo

from Products.PloneFormGen.config import DOWNLOAD_SAVED_PERMISSION
from collective.xlspfgadapter.config import PROJECTNAME


class FormXLSSaveDataFile(ATFile):

    security = ClassSecurityInfo()
    security.declareProtected(DOWNLOAD_SAVED_PERMISSION, 'index_html')

    def SearchableText(self):
        return self.Title()

registerATCT(FormXLSSaveDataFile, PROJECTNAME)
