# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from odoo.osv import expression

class Product_Template_Custom(models.Model):

    _inherit = 'product.template'

    x_manufacturer_code = fields.Char(string="Código fabricante")

    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        if args:
            for arg in args:
                if 'barcode' in arg and len(arg) == 3:
                    stock_packaging = self.env['product.packaging'].search([('barcode',arg[1],arg[2])])
                    product_ids = list(data['product_id'].id for data in stock_packaging)
                    _logger.info("product_ids: \n\n %s \n\n", product_ids)
                    args = expression.OR([[('product_variant_ids', 'in', product_ids)], list(args)])
        return super(Product_Template_Custom, self)._search(args, offset=offset, limit=limit, order=order, count=count, access_rights_uid=access_rights_uid)