from odoo import api, fields, models


class StockPicking_Custom(models.Model):
    _inherit = 'stock.picking.type'

    def get_action_picking_tree_ready_kanban(self):
        response = super(StockPicking_Custom, self).get_action_picking_tree_ready_kanban()
        is_intersect_context = response.get('context')
        
        if self.name == 'Órdenes de entrega':
            is_intersect_context.update({'search_default_picking_type_id': 0})
            is_intersect_context.update({'default_picking_type_id': 0})
            is_intersect_context.update({'search_default_state': 0})
            is_intersect_context.update({'default_state': 0})
            is_intersect_context.update({'search_default_available': 1})
            is_intersect_context.update({'search_default_draft': 1})
            is_intersect_context.update({'search_default_waiting': 1})
            is_intersect_context.update({'search_default_origin': 0})
            is_intersect_context.update({'default_origin': 0})
            is_intersect_context.update({'search_default_group_origin': 1})
            is_intersect_context.update({'group_by': 'origin'})
        return response