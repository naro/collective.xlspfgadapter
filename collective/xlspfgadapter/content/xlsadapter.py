""" A form action adapter that saves form submissions for download """

__author__  = 'Radim Novotny <novotny.radim@gmail.com>'
__docformat__ = 'plaintext'

from AccessControl import ClassSecurityInfo
import logging
import time

from DateTime import DateTime
from types import StringTypes, ListType
from zope.interface import implements

from BTrees.IOBTree import IOBTree
try:
    from BTrees.LOBTree import LOBTree
    SavedDataBTree = LOBTree
except ImportError:
    SavedDataBTree = IOBTree
from BTrees.Length import Length

from Products.Archetypes import atapi
from Products.CMFCore.permissions import ModifyPortalContent
from Products.CMFPlone.utils import base_hasattr, safe_hasattr

from Products.ATContentTypes.content.base import registerATCT

from Products.PloneFormGen.config import DOWNLOAD_SAVED_PERMISSION
from Products.PloneFormGen.config import LP_SAVE_TO_CANONICAL
from Products.PloneFormGen import PloneFormGenMessageFactory as _
from Products.PloneFormGen.content.actionAdapter import \
    FormActionAdapter, FormAdapterSchema

from collective.xlspfgadapter.config import PROJECTNAME
from collective.xlspfgadapter.interfaces import IFormXLSSaveDataAdapter


from zope.contenttype import guess_content_type
logger = logging.getLogger("PloneFormGen")    

import xlwt

ExLinesField = atapi.LinesField


class FormXLSSaveDataAdapter(FormActionAdapter):
    """A form action adapter that will save form input data and 
       return it in XLS format.
       Based on FormXLSSaveDataAdapter
       """
    implements(IFormXLSSaveDataAdapter)
    
    schema = FormAdapterSchema.copy() + atapi.Schema((
        atapi.LinesField('ExtraData',
            widget=atapi.MultiSelectionWidget(
                label=_(u'label_savedataextra_text', default='Extra Data'),
                description=_(u'help_savedataextra_text', default=u"""
                    Pick any extra data you'd like saved with the form input.
                    """),
                format='checkbox',
                ),
            vocabulary = 'vocabExtraDataDL',
            ),
        atapi.BooleanField("UseColumnNames",
            required=False,
            searchable=False,
            widget=atapi.BooleanWidget(
                label = _(u'label_usecolumnnames_text', default=u"Include Column Names"),
                description = _(u'help_usecolumnnames_text', default=u"Do you wish to have column names on the first line of downloaded input?"),
                ),
            ),
    ))

    schema.moveField('execCondition', pos='bottom')

    security       = ClassSecurityInfo()

    def _setupStorage(self):
        set_up =  base_hasattr(self, '_inputStorage') and \
                  base_hasattr(self, '_inputItems') and \
                  base_hasattr(self, '_length')

        if not set_up:
            self._inputStorage = SavedDataBTree()
            self._inputItems = 0
            self._length = Length()


    security.declarePrivate('clear')
    def clear(self):
        self._inputStorage.clear()
        self._inputItems = 0
        self._length.set(0)

    security.declareProtected(DOWNLOAD_SAVED_PERMISSION, 'listData')
    def listData(self):
        for item in self._inputStorage.values():
            yield item
        
    def _addDataRow(self, value):

        self._setupStorage()
        if isinstance(self._inputStorage, IOBTree):
            # 32-bit IOBTree; use a key which is more likely to conflict
            # but which won't overflow the key's bits
            id = self._inputItems
            self._inputItems += 1
        else:
            # 64-bit LOBTree
            id = int(time.time() * 1000)
            while id in self._inputStorage: # avoid collisions during testing
                id += 1
        self._inputStorage[id] = value
        self._length.change(1)

    security.declareProtected(ModifyPortalContent, 'addDataRow')
    def addDataRow(self, value):
        """ a wrapper for the _addDataRow method """
        
        self._addDataRow(value)

    
    def onSuccess(self, fields, REQUEST=None, loopstop=False):
        """
        saves data.
        """

        if LP_SAVE_TO_CANONICAL and not loopstop:
            # LinguaPlone functionality:
            # check to see if we're in a translated
            # form folder, but not the canonical version.
            parent = self.aq_parent
            if safe_hasattr(parent, 'isTranslation') and \
               parent.isTranslation() and not parent.isCanonical():
                # look in the canonical version to see if there is
                # a matching (by id) save-data adapter.
                # If so, call its onSuccess method
                cf = parent.getCanonical()
                target = cf.get(self.getId())
                if target is not None and target.meta_type == 'FormXLSSaveDataAdapter':
                    target.onSuccess(fields, REQUEST, loopstop=True)
                    return

        from ZPublisher.HTTPRequest import FileUpload

        data = []
        for f in fields:
            if f.isFileField():
                file = REQUEST.form.get('%s_file' % f.fgField.getName())
                if isinstance(file, FileUpload) and file.filename != '':
                    file.seek(0)
                    fdata = file.read()
                    filename = file.filename
                    mimetype, enc = guess_content_type(filename, fdata, None)
                    if mimetype.find('text/') >= 0:
                        # convert to native eols
                        fdata = fdata.replace('\x0d\x0a', '\n').replace('\x0a', '\n').replace('\x0d', '\n')
                        data.append( '%s:%s:%s:%s' %  (filename, mimetype, enc, fdata) )
                    else:
                        data.append( '%s:%s:%s:Binary upload discarded' %  (filename, mimetype, enc) )
                else:
                    data.append( 'NO UPLOAD' )
            elif not f.isLabel():
                val = f.htmlValue(REQUEST)
                data.append(val)

        if self.ExtraData:
            for f in self.ExtraData:
                if f == 'dt':
                    data.append( str(DateTime()) )
                else:
                    data.append( getattr(REQUEST, f, '') )

        self._addDataRow( data )


    security.declareProtected(DOWNLOAD_SAVED_PERMISSION, 'getColumnNames')
    def getColumnNames(self):
        """Returns a list of column names"""
        
        names = [field.getName() for field in self.fgFields(displayOnly=True)]
        for f in self.ExtraData:
            names.append(f)
        
        return names

    security.declareProtected(DOWNLOAD_SAVED_PERMISSION, 'getColumnTitles')
    def getColumnTitles(self):
        """Returns a list of column titles"""
        
        names = [field.widget.label for field in self.fgFields(displayOnly=True)]
        for f in self.ExtraData:
            names.append(self.vocabExtraDataDL().getValue(f, ''))
        
        return names

    def vocabExtraDataDL(self):
        """ returns vocabulary for extra data """

        return atapi.DisplayList( (
                ('dt',
                    self.translate( msgid='vocabulary_postingdt_text',
                    domain='ploneformgen',
                    default='Posting Date/Time')
                    ),
                ('HTTP_X_FORWARDED_FOR','HTTP_X_FORWARDED_FOR',),
                ('REMOTE_ADDR','REMOTE_ADDR',),
                ('HTTP_USER_AGENT','HTTP_USER_AGENT',),
                ) )



registerATCT(FormXLSSaveDataAdapter, PROJECTNAME)
