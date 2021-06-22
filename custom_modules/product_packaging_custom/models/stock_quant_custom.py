# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import fields, models, api

_logger = logging.getLogger(__name__)

class Stock_Quant_Custom(models.Model):

    _inherit = 'stock.quant'

    x_units_format = fields.Float(string="Unidades (formato)", compute="_compute_x_units_format")
    
    def _compute_x_units_format(self):
        for record in self:
            if record.package_id:
                packaging_id = self.env['product.packaging'].search([('x_package','=',record.package_id.id)], limit=1)
                record.x_units_format = (record.inventory_quantity or 0) / (packaging_id.qty if packaging_id.qty != 0 else 1)
            else:
                record.x_units_format = 0