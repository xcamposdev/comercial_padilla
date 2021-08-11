# -*- coding: utf-8 -*-
from odoo import fields, models, _
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.exceptions import UserError

class package_barcode_so_custom_stock_picking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'barcodes.barcode_events_mixin']

    def get_barcode_view_state(self):
        """ Return the initial state of the barcode view as a dict.
        """
        pickings = super().get_barcode_view_state()
        for picking in pickings:
            picking['actionReportBultoId'] = self.env.ref('package_barcode_so_custom.action_report_package_sale_order').id
        return pickings


    def put_in_pack(self):
        self.ensure_one()
        if self.state not in ('done', 'cancel'):
            picking_move_lines = self.move_line_ids
            if (
                not self.picking_type_id.show_reserved
                and not self.env.context.get('barcode_view')
            ):
                picking_move_lines = self.move_line_nosuggest_ids

            if self.sale_id and self.sale_id.warehouse_id and self.sale_id.warehouse_id and \
                self.sale_id.warehouse_id.pick_type_id and self.sale_id.warehouse_id.pick_type_id.id and \
                self.sale_id.warehouse_id.pick_type_id.id == self.picking_type_id.id:
                move_line_ids = picking_move_lines.filtered(lambda ml:
                    float_compare(ml.qty_done, 0.0, precision_rounding=ml.product_uom_id.rounding) > 0
                    and not ml.x_package_processed
                )
            else:
                move_line_ids = picking_move_lines.filtered(lambda ml:
                    float_compare(ml.qty_done, 0.0, precision_rounding=ml.product_uom_id.rounding) > 0
                    and not ml.result_package_id
                )

            if not move_line_ids:
                move_line_ids = picking_move_lines.filtered(lambda ml: float_compare(ml.product_uom_qty, 0.0,
                                     precision_rounding=ml.product_uom_id.rounding) > 0 and float_compare(ml.qty_done, 0.0,
                                     precision_rounding=ml.product_uom_id.rounding) == 0)
            if move_line_ids:
                res = self._pre_put_in_pack_hook(move_line_ids)
                if not res:
                    res = self._put_in_pack(move_line_ids)
                return res
            else:
                raise UserError(_("Please add 'Done' qantitites to the picking to create a new pack."))

    def _put_in_pack(self, move_line_ids):
        if self.sale_id and self.sale_id.warehouse_id and self.sale_id.warehouse_id and \
            self.sale_id.warehouse_id.pick_type_id and self.sale_id.warehouse_id.pick_type_id.id and \
            self.sale_id.warehouse_id.pick_type_id.id == self.picking_type_id.id:

            sequence = self.env.ref("package_barcode_so_custom.seq_x_package_barcode_so_custom")
            name = sequence and sequence.next_by_id() or '/'

            package = False
            for pick in self:
                move_lines_to_pack = self.env['stock.move.line']
                package = self.env['stock.quant.package'].create({'name':name})

                precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                if float_is_zero(move_line_ids[0].qty_done, precision_digits=precision_digits):
                    for line in move_line_ids:
                        line.qty_done = line.product_uom_qty

                for ml in move_line_ids:
                    if float_compare(ml.qty_done, ml.product_uom_qty, precision_rounding=ml.product_uom_id.rounding) >= 0:
                        move_lines_to_pack |= ml
                    else:
                        quantity_left_todo = float_round(ml.product_uom_qty - ml.qty_done, precision_rounding=ml.product_uom_id.rounding, rounding_method='UP')
                        done_to_keep = ml.qty_done
                        new_move_line = ml.copy(
                            default={'product_uom_qty': 0, 'qty_done': ml.qty_done})
                        vals = {'product_uom_qty': quantity_left_todo, 'qty_done': 0.0}
                        if pick.picking_type_id.code == 'incoming':
                            if ml.lot_id:
                                vals['lot_id'] = False
                            if ml.lot_name:
                                vals['lot_name'] = False
                        ml.write(vals)
                        new_move_line.write({'product_uom_qty': done_to_keep})
                        move_lines_to_pack |= new_move_line
                package_level = self.env['stock.package_level'].create({
                    'package_id': package.id,
                    'picking_id': pick.id,
                    'location_id': False,
                    'location_dest_id': move_line_ids.mapped('location_dest_id').id,
                    'move_line_ids': [(6, 0, move_lines_to_pack.ids)],
                    'company_id': pick.company_id.id,
                })
                move_lines_to_pack.write({
                    'result_package_id': package.id,
                    'x_package_processed': True
                })
            return package
        else:
            return super(package_barcode_so_custom_stock_picking, self)._put_in_pack(move_line_ids)

    def get_packaging_report_packaging(self):
        toreturn = list()

        # Get Company Logo
        company = self.env['res.company'].search([], order="id asc")

        for record in self:
            for line in record.move_line_ids_without_package or []:
                if line.result_package_id:
                    data_find = list(data for data in toreturn if data['package_id'] == line.result_package_id.id)
                    if not data_find:
                        toreturn.append({
                            'company_id': company[1].id if record.partner_id.x_is_tss else company[0].id,
                            'company_name': company[1].name if record.partner_id.x_is_tss else company[0].name,
                            'company_vat': company[1].vat if record.partner_id.x_is_tss else company[0].vat,

                            'company': company[1].partner_id if record.partner_id.x_is_tss else company[0].partner_id,
                            'partner': record.partner_id,

                            'carrier_name': record.carrier_id.name,
                            'weight': float(line.product_id.weight * line.product_uom_qty),
                            'weight_uom_name': line.product_id.weight_uom_name,

                            'package_id': line.result_package_id.id,
                            'package_name': line.result_package_id.name,
                            'sale_name': record.sale_id.name if record.sale_id else '',
                            'picking_name': record.name,
                        })
                    else:
                        data_find[0]['weight'] = float(data_find[0]['weight']) + (line.product_id.weight * line.product_uom_qty)
                        #data_find['weight'] = float(data_find['weight']) + (line.product_id.weight * line.product_uom_qty)

        return toreturn

class package_barcode_so_custom_stock_picking(models.Model):
    
    _inherit = 'stock.move.line'

    x_package_processed = fields.Boolean(default=False)