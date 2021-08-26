# -*- coding: utf-8 -*-
from odoo import models


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'barcodes.barcode_events_mixin']

    def has_origin(self):
        return True if self.origin else False
