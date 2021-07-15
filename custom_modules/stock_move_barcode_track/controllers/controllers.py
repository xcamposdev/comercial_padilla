from odoo import http, _
from odoo.http import request
from odoo.addons.stock_barcode.controllers.main import StockBarcodeController


class StockBarcodeControllerCustom(StockBarcodeController):

    @http.route('/stock_barcode/scan_from_main_menu', type='json', auth='user')
    def main_menu(self, barcode, **kw):
        """ Receive a barcode scanned from the main menu and return the appropriate
            action (open an sale or existing / new picking) or warning.
        """
        try_open_sale_order = StockBarcodeControllerCustom.try_open_sale_order(barcode)
        if try_open_sale_order:
            return try_open_sale_order
        super(StockBarcodeControllerCustom, self).main_menu(barcode, **kw)

    @staticmethod
    def try_open_sale_order(barcode):
        """ If barcode represent a sale type, open the sale"""
        sale_order = request.env['sale.order'].search([
            ('name', '=', barcode)
        ], limit=1)
        if sale_order:
            view_id = request.env.ref('sale.view_order_form').id
            return {
                'action': {
                    'name': _('Open Order form'),
                    'res_model': 'sale.order',
                    'view_mode': 'form',
                    'view_id': view_id,
                    'views': [(view_id, 'form')],
                    'type': 'ir.actions.act_window',
                    'res_id': sale_order.id,
                }
            }
        return False
