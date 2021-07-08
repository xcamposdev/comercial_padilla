import logging
import threading
from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MaterialDeliverySaleOrder(models.Model):
    _inherit = "sale.order"
    _description = "Personalizar Entrega"
    _auto = False

    execute_cron = False

    def action_confirm(self):
        """ This method extends the actual behavior adding an automatic option to create
        stock moves to restock the quantity needed.

        :return: bool
        """
        sale = super(MaterialDeliverySaleOrder, self).action_confirm()
        if self.warehouse_id.delivery_steps != 'pick_pack_ship' and not self.warehouse_id.x_auto_re_stock:
            return sale
        stock_id = self.warehouse_id.lot_stock_id.id
        stock_quantity = self.env['stock.quant']
        for move_line in self.order_line:
            requested_qty = move_line.product_uom_qty
            stock_quantity = stock_quantity.search(
                [('location_id', '=', stock_id), ('product_id', '=', move_line.product_id.id),
                 ('quantity', '>=', move_line.product_uom_qty)])
            if len(list(stock_quantity)) > 0 and \
                    (stock_quantity.quantity - stock_quantity.reserved_quantity) > requested_qty:
                pass
            else:
                # review if the location_id has to be always field usage = internal
                # review if the location_id isn't related to the warehouse target
                packaging_ids = self.env['product.packaging'].search(
                    [('product_id', '=', move_line.product_id.id)], order='qty desc')
                move_ref = self.env['stock.move'].search([
                    ('product_id', '=', move_line.move_ids[0].product_id.id),
                    ('origin', '=', move_line.move_ids[0].origin)], limit=1)
                for pack in packaging_ids:
                    if not pack.x_location:
                        raise UserError('El empaquetado "%s" no tiene asignado una ubicación para el producto "%s"' % (
                            pack.name, move_line.product_id.name))
                    stock_quantity = stock_quantity.search(
                        [('location_id', '=', pack.x_location.id), ('product_id', '=', move_line.product_id.id),
                         ('package_id', '=', pack.x_package.id),
                         ('quantity', '>=', pack.qty)], limit=1)
                    location_id = stock_quantity.location_id.id
                    packs_requested = MaterialDeliverySaleOrder._get_available_per_pack(
                        requested_qty, stock_quantity.quantity - stock_quantity.reserved_quantity, pack.qty)
                    if packs_requested != 0:
                        picking_id = self.create_stock_piking_material_delivery(move_ref, location_id, stock_id)
                        self._generate_move_lines(move_ref, picking_id, stock_quantity,
                                                  packs_requested, location_id, stock_id, pack.x_package.id)
                        picking_id.action_confirm()
                        requested_qty -= packs_requested

                if requested_qty > 0:
                    stock_quantity = stock_quantity.search(
                        [('location_id', 'not in', [
                            self.warehouse_id.view_location_id.id,
                            self.warehouse_id.lot_stock_id.id,
                            self.warehouse_id.wh_input_stock_loc_id.id,
                            self.warehouse_id.wh_qc_stock_loc_id.id,
                            self.warehouse_id.wh_pack_stock_loc_id.id,
                            self.warehouse_id.wh_output_stock_loc_id.id,
                        ]), ('product_id', '=', move_line.product_id.id),
                         ('quantity', '>', 0)])
                    requested_qty = self._generate_extra_moves_by_location(stock_quantity, move_ref, requested_qty,
                                                                           stock_id)
                    if requested_qty > 0:
                        MaterialDeliverySaleOrder.execute_cron = True

        if MaterialDeliverySaleOrder.execute_cron:
            ssc = self.env['stock.scheduler.compute']
            threaded_calculation = threading.Thread(target=ssc._procure_calculation_orderpoint, args=())
            threaded_calculation.start()

        return sale

    @staticmethod
    def _get_available_per_pack(requested_qty, available, pack_qty):
        if requested_qty == 0 or available == 0 or pack_qty > requested_qty:
            return 0
        result = 0
        vals = range(0, int(requested_qty))
        values = [vals[i:i + int(pack_qty)] for i in range(0, len(vals), int(pack_qty))]
        if len(values[-1]) != int(pack_qty):
            del values[-1]
        for pack in values:
            if available >= pack_qty:
                available -= pack_qty
                result += pack_qty
            else:
                break
        return result

    def _generate_extra_moves_by_location(self, available_locations, move_ref, requested_qty, stock_id):
        for squant in available_locations:
            location_id = squant.location_id.id
            available_qty = squant.quantity - squant.reserved_quantity
            picking_id = self.create_stock_piking_material_delivery(move_ref, location_id, stock_id)
            if available_qty >= requested_qty:
                self._generate_move_lines(move_ref, picking_id, squant, requested_qty, location_id, stock_id)
                picking_id.action_confirm()
                requested_qty = 0
                break
            else:
                self._generate_move_lines(move_ref, picking_id, squant, available_qty, location_id, stock_id)
                picking_id.action_confirm()
                requested_qty -= available_qty
        return requested_qty

    def _generate_move_lines(self, last_move, picking_id, quant, quantity, location_id, location_dest_id,
                             packaging_id=None, package_level=None):
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
            'procure_method': 'make_to_stock',
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
            'x_packaging': packaging_id,
        })
        move._action_confirm()

    def create_stock_piking_material_delivery(self, last_move, location_id, dest_location_id):
        stock_picking_values = {
            'partner_id': self.partner_id.id,
            'picking_type_id': self._get_stock_picking_type(location_id, dest_location_id),
            'location_id': location_id,
            'location_dest_id': dest_location_id,
            'scheduled_date': last_move.date,
            'origin': last_move.origin,
            'sale_id': self.id,
            'group_id': last_move.group_id.id,
        }
        res = self.env['stock.picking'].create(stock_picking_values)
        return res

    def _get_stock_picking_type(self, location_id, dest_location_id):
        picking_type = self.env['stock.picking.type']
        picking_type_id = picking_type.search(
            [('code', '=', 'internal'), ('warehouse_id', '=', self.warehouse_id.id), ('sequence_code', '=', 'INT')])
        if len(list(picking_type_id)) > 0:
            _logger.debug('The stock.picking.type transit was found to generate stock.pickins %s', picking_type_id)
            return picking_type_id.id
        else:
            res = picking_type.create({
                'name': 'suplir falta de stock',
                'code': 'internal',
                'warehouse_id': self.warehouse_id.id,
                'default_location_src_id': location_id,
                'default_location_dest_id': dest_location_id,
                'sequence_code': 'INT-TRANSIT',
            })
            _logger.info('The new stock.picking.type transit was creaded %s', res.id)
            return res.id
