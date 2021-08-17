from odoo import fields, models, api
import logging

_logger = logging.getLogger(__name__)

class SaleOrder_stockbacode(models.Model):
    
    _inherit = "sale.order"

    x_partner_id_x_is_tss = fields.Boolean(string='¿Es TSS?', compute="_compute_get_partner_x_is_tss")
    x_picking_count = fields.Integer(string='Nro of picks', compute='_compute_number_picks')
    x_item_count = fields.Integer(string='Nro of items', compute='_compute_number_items')
    x_unit_total = fields.Integer(string='Nro of units', compute='_compute_number_units')
    x_weight_total = fields.Float(string="Weight total", compute="_compute_weight_total")
    
    def _compute_get_partner_x_is_tss(self):
        for record in self:
            record.x_partner_id_x_is_tss = record.partner_id.x_is_tss

    @api.depends('picking_ids')
    def _compute_number_picks(self):
        for order in self:
            if order.warehouse_id:
                picks = list(data for data in order.picking_ids if data.picking_type_id == order.warehouse_id.pick_type_id)
                order.x_picking_count = len(picks)

    def _compute_number_items(self):
        for order in self:
            order.x_item_count = sum(1 if data.product_id else 0 for data in order.order_line)

    def _compute_number_units(self):
        for order in self:
            order.x_unit_total = sum(data.product_uom_qty for data in order.order_line)

    def _compute_weight_total(self):
         for order in self:
            order.x_weight_total = sum(data.product_id.weight * data.product_uom_qty if data.product_id else 0 for data in order.order_line)