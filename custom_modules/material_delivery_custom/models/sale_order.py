
import logging
#from server.odoo.fields import Float

from odoo import api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class material_delivery_sale_order(models.Model):
    
    _inherit = "sale.order"
    _description = "Personalizar Entrega"
    _auto = False

    def action_confirm(self):
        sale = super(material_delivery_sale_order, self).action_confirm()

        #-------------------GENERAR N Movimientos------------------------
        location_default = self.env['ir.config_parameter'].sudo().get_param('x_md_default_location_cornella')
        warehouse_cornella = self.env['ir.config_parameter'].sudo().get_param('x_md_warehouse_cornella')
        operation_type_cornella = int(self.env['ir.config_parameter'].sudo().get_param('x_md_operation_type_cornella'))
        warehouse_cornella = warehouse_cornella.split()
        warehouse_cornella = list(map(int, warehouse_cornella))
        if (self.state == 'sale' or self.state == 'done') and self.warehouse_id.id in warehouse_cornella:
            for line in self.order_line:
                
                product_qty = line.product_uom_qty
                packaging = self.env['product.packaging'].search_read([('product_id','=',line.product_id.id)], fields=['id', 'qty','x_location'],  order='qty desc')
                
                while product_qty > 0:
                    if packaging and len(packaging):
                        
                        packing_qty = 0
                        while product_qty > float(packaging[0]['qty']):
                            packing_qty += float(packaging[0]['qty'])
                            product_qty -= float(packaging[0]['qty'])

                        if packing_qty != 0:
                            #raise UserError('Mensaje de error')
                            if packaging[0]['x_location'] ==False:
                                packaging[0]['x_location'] = [int(location_default)]
                            self.create_aditional_material_delivery(line, operation_type_cornella, packaging[0]['x_location'][0], packing_qty, warehouse_cornella)
                        packaging.pop(0)
                    else:
                        self.create_aditional_material_delivery(line, operation_type_cornella, int(location_default), product_qty, warehouse_cornella)
                        break
        #----------------------------------------------------------------
        return sale
        #que sucede si no tiene localizacion el paquete

    def create_aditional_material_delivery(self, line, operation_type_cornella, locationId, qty, warehouse_cornella):
        move_search = self.env['stock.move'].search([
            ('product_id','=',line.move_ids[0].product_id.id),
            ('product_qty','=',line.move_ids[0].product_qty),
            ('origin','=',line.move_ids[0].origin),
            '|',('state','=','confirmed'),('state','=','assigned')
            ])
        moves_values = {
            'name': move_search.name,
            'product_id': move_search.product_id.id,
            'product_uom': move_search.product_uom.id,
            'location_id': locationId,
            'location_dest_id': move_search.location_id.id,
            'product_uom_qty': qty,
            'partner_id': move_search.partner_id.id,

            'move_dest_ids':move_search.move_dest_ids,
            'rule_id':False,
            'procure_method':move_search.procure_method,
            'origin': line.move_ids[0].origin,
            'picking_type_id':operation_type_cornella,
            'group_id':move_search.group_id.id,
            'route_ids':move_search.route_ids.ids,
            'warehouse_id':move_search.warehouse_id.id,
            'date':move_search.date,
            'date_expected':move_search.date,
            'propagate_cancel':move_search.propagate_cancel,
            'propagate_date':move_search.propagate_date,
            'propagate_date_minimum_delta':move_search.propagate_date_minimum_delta,
            'description_picking':move_search.description_picking,
            'priority':move_search.priority,
            'delay_alert':move_search.delay_alert,
            'sale_line_id':False,
        }
        move = self.env['stock.move'].sudo().create(moves_values)
        move._action_confirm()
