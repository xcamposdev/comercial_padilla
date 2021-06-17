# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from psycopg2 import OperationalError, Error

class Stock_Quant_Custom(models.Model):

    _inherit = 'stock.quant'

    x_units_format = fields.Float(string="Unidades (formato)", compute="_compute_x_units_format")
    
    def _compute_x_units_format(self):
        for record in self:
            if record.package_id:
                packaging_id = self.env['product.packaging'].search([('id','=',record.package_id.id)], limit=1)
                record.x_units_format = (packaging_id.qty or 0) / (record.inventory_quantity if record.inventory_quantity != 0 else 1)
            else:
                record.x_units_format = 0