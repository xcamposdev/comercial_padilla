# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.exceptions import ValidationError

class Product_Template_Price_Custom(models.Model):

    _inherit = 'product.template'

    x_list_price_sale = fields.One2many('product.pricelist.item', string='Márgenes x tarifa', compute="_compute_x_list_price_sale")

    def _compute_x_list_price_sale(self):
        for record in self:
            product_pricelist_items = self.env['product.pricelist.item'].search([('product_tmpl_id','=',record.id)])
            if product_pricelist_items and len(product_pricelist_items):
                for data in product_pricelist_items:
                    data.x_price = data.price
                    if data.compute_price == 'fixed':
                        data.x_price_cost_difference = data.fixed_price - record.standard_price
                        data.x_percent_margin_sale = ((data.fixed_price - record.standard_price) / (data.fixed_price if data.fixed_price != 0 else 1)) * 100
                    elif data.compute_price == 'percentage':
                        price_sale = (record.list_price - (data.percent_price * record.list_price / 100))
                        data.x_price_cost_difference = price_sale - record.standard_price
                        data.x_percent_margin_sale = ((price_sale - record.standard_price) / (price_sale if price_sale != 0 else 1)) * 100
                    elif data.compute_price == 'formula':
                        price_sale = (record.list_price - (data.price_discount * record.list_price / 100) + data.price_surcharge)
                        data.x_price_cost_difference = price_sale - record.standard_price
                        data.x_percent_margin_sale = ((price_sale - record.standard_price) / (price_sale if price_sale != 0 else 1)) * 100
                record.x_list_price_sale = product_pricelist_items
            else:
                record.x_list_price_sale = False

class PricelistItem_custom(models.Model):

    _inherit = "product.pricelist.item"

    x_price = fields.Char(string="Precio")
    x_price_cost_difference = fields.Float(string="Margen")
    x_percent_margin_sale = fields.Float(string="% margen")