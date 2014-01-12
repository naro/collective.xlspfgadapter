"""
Tests for the save as document pfg adapter.
Taken
"""

import os, sys, email

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Products.CMFCore.utils import getToolByName
from collective.documentpfgadapter.tests.base import TestCase
from Products.CMFPlone.utils import _createObjectByType

# dummy class
class cd:
    pass

class FakeRequest(dict):

    def __init__(self, **kwargs):
        self.form = kwargs

class TestAdapter(TestCase):

    def afterSetUp(self):
        self.folder.invokeFactory('FormFolder', 'ff1')
        self.ff1 = getattr(self.folder, 'ff1')
        self.folder.invokeFactory('Folder', 'docs')
        self.docs = getattr(self.folder, 'docs')


    def testSaver(self):
        """ test save data adapter action """


        _createObjectByType('FormSaveDocumentAdapter', self.ff1, id='saver', title='Saver')

        self.failUnless('saver' in self.ff1.objectIds())
        self.ff1.saver.setSaveLocation(self.docs)

        saver = self.ff1.saver

        self.ff1.setActionAdapter( ('saver',) )
        self.assertEqual(self.ff1.actionAdapter, ('saver',))

        # print "|%s|" % saver.SavedFormInput

        self.assertEqual(len(self.docs.objectIds()), 0)

        request = FakeRequest(topic = 'test subject', replyto='test@test.org', comments='test comments')
        errors = self.ff1.fgvalidate(REQUEST=request)
        self.assertEqual( errors, {} )

        self.assertEqual(len(self.docs.objectIds()), 1)

        doc_id = self.docs.objectIds()[0]
        doc = getattr(self.docs, doc_id)
        body = doc.CookedBody()
        
        self.failUnless('test subject' in body)
        self.failUnless('test@test.org' in body)
        self.failUnless('test comments' in body)


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestAdapter))
    return suite
