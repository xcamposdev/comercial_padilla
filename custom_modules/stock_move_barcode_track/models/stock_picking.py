# -*- coding: utf-8 -*-
from odoo import models


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'barcodes.barcode_events_mixin']

    def get_barcode_view_state(self):
        """ Return the initial state of the barcode view as a dict.
        """
        pickings = super(StockPicking, self).get_barcode_view_state()
        for picking in pickings:
            picking['actionReportMatriculaId'] = self.env.ref('stock_move_barcode_track.action_report_registration_order').id
        return pickings
