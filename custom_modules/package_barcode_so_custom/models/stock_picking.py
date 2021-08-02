# -*- coding: utf-8 -*-
from odoo import models
from odoo.tools.float_utils import float_compare, float_is_zero, float_round

class package_barcode_so_custom_stock_picking(models.Model):

    _inherit = 'stock.picking'

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
                })
            return package
        else:
            return super(package_barcode_so_custom_stock_picking, self)._put_in_pack(move_line_ids)

    def get_packaging_report_packaging(self):
        toreturn = list()
        for record in self:
            for line in record.move_line_ids_without_package or []:
                if line.result_package_id:
                    data_find = list(data for data in toreturn if data['package'] == line.result_package_id.id)
                    if data_find:
                        data_find['lines'].append({ 'product': data_find.product_id.display_name, 'quantity': data_find.qty_done })
                    else:
                        toreturn.append({ 
                            'package': line.result_package_id.name,
                            'sale': record.sale_id.name if record.sale_id else '',
                            'picking': record.name,
                            'address': record.partner_id,
                            'partner': record.partner_id.display_name,
                            'lines': [{ 'product': line.product_id.display_name, 'quantity': line.qty_done }]
                        })

        return toreturn
