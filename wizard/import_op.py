# -*- coding: utf-8 -*-
import itertools
import datetime

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

try:
    import xlrd

    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None


class ImportOp(models.TransientModel):
    _name = "mrp.import.op"
    _description = "Lanza una ventana para impor tar op's"

    file = fields.Binary('Archivo XLS', required=True)

    def load_file(self):
        book = xlrd.open_workbook(file_contents=self.file.decode('base64'))
        xls_rows = self._read_xls_book(book)
        data_to_create = self._prepare_data(xls_rows)
        order_line = self.env['mrp.order.operation']
        for i in data_to_create:
            order_line.create(i)

    def _prepare_data(self, xls_rows):
        products = [{'codigo': row[0], 'cantidad': row[1], 'destino': row[2]} for i, row in enumerate(xls_rows) if
                    i != 0]
        product_ids = self.env['product.product'].search([('default_code', 'in', [i['codigo'] for i in products])])
        for product in product_ids:
            filter_product = filter(lambda x: x['codigo'] == product.default_code, products)
            yield {
                'order_id': self._context.get('active_id'),
                'product_id': product.id,
                'num_piezas': sum(
                    int(i['cantidad']) for i in filter_product),
                'location_dest_id':
                    self.env['stock.location'].search([('name', 'ilike', filter_product[0]['destino'])])[0].id
            }

    def _read_xls_book(self, book):
        sheet = book.sheet_by_index(0)
        # emulate Sheet.get_rows for pre-0.9.4
        for row in itertools.imap(sheet.row, range(sheet.nrows)):
            values = []
            for cell in row:
                if cell.ctype is xlrd.XL_CELL_NUMBER:
                    is_float = cell.value % 1 != 0.0
                    values.append(
                        unicode(cell.value)
                        if is_float
                        else unicode(int(cell.value))
                    )
                elif cell.ctype is xlrd.XL_CELL_DATE:
                    is_datetime = cell.value % 1 != 0.0
                    # emulate xldate_as_datetime for pre-0.9.3
                    dt = datetime.datetime(*xlrd.xldate.xldate_as_tuple(cell.value, book.datemode))
                    values.append(
                        dt.strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        if is_datetime
                        else dt.strftime(DEFAULT_SERVER_DATE_FORMAT)
                    )
                elif cell.ctype is xlrd.XL_CELL_BOOLEAN:
                    values.append(u'True' if cell.value else u'False')
                elif cell.ctype is xlrd.XL_CELL_ERROR:
                    raise ValueError(
                        _("Error cell found while reading XLS/XLSX file: %s") %
                        xlrd.error_text_from_code.get(
                            cell.value, "unknown error code %s" % cell.value)
                    )
                else:
                    values.append(cell.value)
            if any(x for x in values if x.strip()):
                yield values
