# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api

class Product_Template_Custom(models.Model):

    _inherit = 'product.template'

    x_manufacturer_code = fields.Char(string="Código fabricante")
    x_product_packaging = fields.Char(string="Empaquetado (código de barras)", search="_search_product_packaging", compute='_compute_product_packaging')

    def _compute_product_packaging(self):
        for record in self:
            record.x_product_packaging = ""

    def _search_product_packaging(self, operator, value):
        stock_packaging = self.env['product.packaging'].search([('barcode',operator,value)])
        product_ids = list(data['product_id'].id for data in stock_packaging)
        return [('product_variant_ids','in',product_ids)]