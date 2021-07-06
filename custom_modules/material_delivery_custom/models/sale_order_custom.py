import logging
import threading
from odoo import models

_logger = logging.getLogger(__name__)


class material_delivery_sale_order(models.Model):
    _inherit = "sale.order"
    _description = "Personalizar Entrega"
    _auto = False

    execute_cron = False

    def action_confirm(self):
        """ This method extends the actual behavior adding an automatic option to create
        stock moves to restock the quantity needed.

        :return: bool
        """
        sale = super(material_delivery_sale_order, self).action_confirm()
        # unused for now
        steps = self.warehouse_id.delivery_steps
        stock_id = self.warehouse_id.lot_stock_id.id
        StockQuantity = self.env['stock.quant']
        picking_ids = []
        for move_line in self.order_line:
            requested_qty = move_line.product_uom_qty
            StockQuantity = StockQuantity.search(
                [('location_id', '=', stock_id), ('product_id', '=', move_line.product_id.id),
                 ('quantity', '>=', move_line.product_uom_qty)])
            if len(list(StockQuantity)) > 0:
                pass
            else:
                # review if the location_id has to be always field usage = internal
                # review if the location_id isn't related to the warehouse target
                StockQuantity = StockQuantity.search(
                    [('location_id', 'not in', [
                        self.warehouse_id.view_location_id.id,
                        self.warehouse_id.lot_stock_id.id,
                        self.warehouse_id.wh_input_stock_loc_id.id,
                        self.warehouse_id.wh_qc_stock_loc_id.id,
                        self.warehouse_id.wh_pack_stock_loc_id.id,
                        self.warehouse_id.wh_output_stock_loc_id.id,
                    ]), ('product_id', '=', move_line.product_id.id),
                     ('quantity', '>', 0)])

                for squant in StockQuantity:
                    location_id = squant.location_id.id
                    available_qty = squant.quantity
                    move_search = self.env['stock.move'].search([
                        ('product_id', '=', move_line.move_ids[0].product_id.id),
                        ('product_qty', '=', move_line.move_ids[0].product_qty),
                        ('origin', '=', move_line.move_ids[0].origin),
                        '|', ('state', '=', 'confirmed'), ('state', '=', 'assigned')
                    ])
                    if available_qty >= requested_qty:
                        picking_id = self.create_stock_piking_material_delivery(move_search, location_id, self.warehouse_id, stock_id)
                        self._generate_move_lines(move_search, picking_id, squant, requested_qty, location_id, stock_id)
                        requested_qty = 0
                        picking_id.action_confirm()
                        picking_ids.append(picking_id.id)
                        break
                    else:
                        picking_id = self.create_stock_piking_material_delivery(move_search, location_id,
                                                                                self.warehouse_id, stock_id)
                        self._generate_move_lines(move_search, picking_id, squant, available_qty, location_id, stock_id)
                        picking_id.action_confirm()
                        picking_ids.append(picking_id.id)
                        requested_qty -= available_qty

                if requested_qty > 0:
                    material_delivery_sale_order.execute_cron = True

        if material_delivery_sale_order.execute_cron:
            ssc = self.env['stock.scheduler.compute']
            threaded_calculation = threading.Thread(target=ssc._procure_calculation_orderpoint, args=())
            threaded_calculation.start()

        return sale

    def _generate_move_lines(self, last_move, picking_id, quant, quantity, location_id, location_dest_id, package_level=None, company_id=None):
        move = self.env['stock.move'].sudo().create({
            'picking_id': picking_id.id,
            'name': quant.product_id.display_name,
            'product_id': quant.product_id.id,
            'product_uom_qty': quantity,
            'product_uom': quant.product_id.uom_id.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'package_level_id': package_level,
            'origin': last_move.origin,
            'company_id': last_move.company_id.id,
            'partner_id': last_move.partner_id.id,
            'rule_id': False,
            'procure_method': last_move.procure_method,
            'picking_type_id': picking_id.picking_type_id.id,
            'group_id': last_move.group_id.id,
            'date': last_move.date,
            'date_expected': last_move.date,
            'propagate_cancel': last_move.propagate_cancel,
            'propagate_date': last_move.propagate_date,
            'propagate_date_minimum_delta': last_move.propagate_date_minimum_delta,
            'description_picking': last_move.description_picking,
            'priority': last_move.priority,
            'delay_alert': last_move.delay_alert,
            'sale_line_id': False,
        })
        move._action_confirm()

    def create_stock_piking_material_delivery(self, last_move, location_id, warehouse_id, dest_location_id):
        stock_picking_values = {
            'partner_id': self.partner_id.id,
            'picking_type_id': self._get_stock_picking_type(location_id, dest_location_id, warehouse_id),
            'location_id': location_id,
            'location_dest_id': dest_location_id,
            'scheduled_date': last_move.date,
            'origin': last_move.origin,
            'sale_id': self.id,
            'group_id': last_move.group_id.id,
        }
        res = self.env['stock.picking'].create(stock_picking_values)
        return res

    def _get_stock_picking_type(self, location_id, dest_location_id, warehouse_id):
        PickingType = self.env['stock.picking.type']
        picking_type_id = PickingType.search(
            [('code', '=', 'internal'), ('warehouse_id', '=', warehouse_id.id), ('sequence_code', '=', 'INT-TRANSIT')])
        if len(list(picking_type_id)) > 0:
            _logger.debug('The stock.picking.type transit was found to generate stock.pickins %s', picking_type_id)
            return picking_type_id.id
        else:
            res = PickingType.create({
                'name': 'suplir falta de stock',
                'code': 'internal',
                'warehouse_id': warehouse_id.id,
                'default_location_src_id': location_id,
                'default_location_dest_id': dest_location_id,
                'sequence_code': 'INT-TRANSIT',
            })
            _logger.info('The new stock.picking.type transit was creaded %s', res.id)
            return res.id
