from cStringIO import StringIO
from DateTime import DateTime
import datetime
from Products.CMFCore.utils import getToolByName
from Products.PloneFormGen.config import DOWNLOAD_SAVED_PERMISSION
from Acquisition import aq_inner
from Products.Five import BrowserView
import xlwt

XL_DATE_STYLE = xlwt.easyxf(num_format_str='DD.MM.YYYY')
XL_DATETIME_STYLE = xlwt.easyxf(num_format_str='DD.MM.YYYY HH:MM:SS')


def DT2dt(date):
    args = map(int, date.parts()[:6])
    args.append(0)
    return datetime.datetime(*args)


class XLSAdapterView(BrowserView):

    def can_download(self):
        context = aq_inner(self.context)
        mtool = getToolByName(context, 'portal_membership')
        return mtool.checkPermission(DOWNLOAD_SAVED_PERMISSION, context)

    def count(self):
        storage = getattr(self.context, '_inputStorage', [])
        return len(storage)

    def download(self):
        context = aq_inner(self.context)
        form = context.formFolderObject()

        timestamp = datetime.datetime.now().strftime(r"%Y-%m-%d-%H-%M-%S")
        filename = "%s-%s.xls" % (form.getId(), timestamp)

        self.request.response.setHeader('Content-Type', 'application/excel')
        self.request.response.setHeader(
                        'Content-Disposition',
                        'attachment;filename=%s' % filename)
        stream = StringIO()

        wb = xlwt.Workbook(encoding='utf8')
        ws = wb.add_sheet(form.Title())
        row_n = col_n = 0

        ws.set_panes_frozen(True)  # frozen headings instead of split panes
        ws.set_horz_split_pos(row_n + 1)  # in general, freeze after last heading row
        ws.set_remove_splits(True)  # if user does unfreeze, don't leave a split there

        fields = form.fgFields(displayOnly=True)

        for field in fields:
            title = form.findFieldObjectByName(field.getName()).Title()
            ws.write(row_n, col_n, title)
            col_n += 1
        for f in context.getExtraData():
            ws.write(row_n, col_n, f)
            col_n += 1

        # ws.col(7).width = 5000
        row_n += 1
        for row in context.listData():
            col_n = 0
            for field in fields:
                name = field.getName()
                if name in row:
                    value = row[name]
                    typ = field.type
                    if typ == 'datetime':
                        if value:
                            if isinstance(value, basestring):
                                value = DateTime(value, datefmt="en")
                            if value.time == 0.0:
                                format = XL_DATE_STYLE
                            else:
                                format = XL_DATETIME_STYLE
                            ws.write(row_n, col_n, DT2dt(value), format)
                    else:
                        ws.write(row_n, col_n, value)
                else:
                    # not saved - probably field added/removed during time
                    ws.write(row_n, col_n, 'N/A')
                col_n += 1
            for f in context.getExtraData():
                name = 'extra_' + f
                if name in row:
                    value = row[name]
                    if f == 'dt':
                        ws.write(row_n, col_n, DT2dt(DateTime(value)), XL_DATE_STYLE)
                    else:
                        ws.write(row_n, col_n, value)
                else:
                    # not saved - probably field added/removed during time
                    ws.write(row_n, col_n, 'N/A')
                col_n += 1
            row_n += 1

        wb.save(stream)
        return stream.getvalue()


class XLSAdapterClearView(BrowserView):

    def _clear(self):
        """ Clear data """
        context = aq_inner(self.context)
        context.clear()
        context.manage_delObjects(context.objectIds())

    def form_url(self):
        form = self.context.formFolderObject()
        return form.absolute_url()

    def __call__(self):
        context = aq_inner(self.context)
        if self.request.form.get('form.submitted') == '1':
            self._clear()
            form_url = self.form_url()
            ptool = getToolByName(context, 'plone_utils')
            ptool.addPortalMessage('Data has been cleared.')
            return self.request.response.redirect(form_url)
        return self.index()

