
import logging

from odoo import api, fields, models, tools, _

_logger = logging.getLogger(__name__)

class info_sp_so_mobile_stock_picking(models.Model):
    
    _inherit = "stock.picking"

    def get_origin_sale_kanban(self, origin):
        if origin:
            sale = self.env['sale.order'].search([('name','=',origin)], limit=1)
            if sale and sale.order_line:
                weight = 0
                for line in sale.order_line:
                    weight += line.product_id.weight * line.product_uom_qty
                return { 'partner_name': sale.partner_id.display_name, 'is_tss': sale.partner_id.x_is_tss, 'weight': str(weight) + " " + str(line.product_id.weight_uom_name), 'number_of_lines': len(sale.order_line) }
        return False
		
