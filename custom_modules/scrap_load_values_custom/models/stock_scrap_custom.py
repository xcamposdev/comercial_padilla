# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class StockScrapCustom(models.Model):
    _inherit = 'stock.scrap'

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.scrap_qty = self.product_id.qty_available
        else:
            self.scrap_qty = self.scrap_qty
    
    @api.onchange('package_id')
    def onchange_package_id(self):
        if self.package_id:
            self.location_id = self.package_id.location_id

