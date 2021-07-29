# -*- coding: utf-8 -*-
from odoo import models, api


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    def change_source(self, new_location):
        if 'id' in new_location.keys():
            return self.write({'location_ids': [(6, 0, [new_location['id']])]})
        return False
