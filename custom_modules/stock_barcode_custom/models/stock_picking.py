# -*- coding: utf-8 -*-

from odoo import models, fields, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_is_zero, float_compare, float_round

import json


class StockMoveLine(models.Model):
    _name = 'stock.move.line'
    _inherit = ['stock.move.line', 'barcodes.barcode_events_mixin']

    product_barcode = fields.Char(related='product_id.barcode')
    location_processed = fields.Boolean()
    dummy_id = fields.Char(compute='_compute_dummy_id', inverse='_inverse_dummy_id')

    def _compute_dummy_id(self):
        self.dummy_id = ''

    def _inverse_dummy_id(self):
        pass


class StockPicking(models.Model):
    _name = 'stock.picking'
    _inherit = ['stock.picking', 'barcodes.barcode_events_mixin']

    def get_barcode_view_state(self):
        """ Return the initial state of the barcode view as a dict.
        """
        fields_to_read = self._get_picking_fields_to_read()
        pickings = self.read(fields_to_read)
        sale = self.env['sale.order']
        picking_type_ids = []
        if self.origin:
            sale = sale.search([('name', '=', self.origin)])
            if sale.x_inventory_state == 'pick' and self.env.user.x_pick:
                picking_type_ids = [self.sale_id.warehouse_id.pick_type_id.id, self.sale_id.warehouse_id.int_type_id.id]
            if sale.x_inventory_state == 'pack' and self.env.user.x_pack:
                picking_type_ids = [self.sale_id.warehouse_id.pack_type_id.id, self.sale_id.warehouse_id.int_type_id.id]
            if sale.x_inventory_state == 'out' and self.env.user.x_out:
                picking_type_ids = [self.sale_id.warehouse_id.out_type_id.id, self.sale_id.warehouse_id.int_type_id.id]
        picking_ids = self.search([('origin', '=', self.origin),
                                   ('picking_type_id', 'in', picking_type_ids),
                                   ('state', 'not in', ['done', 'cancel'])])

        # Order by location name
        picking_ids = picking_ids.sorted(key=lambda r: r.location_id.name)

        if self not in picking_ids:
            pickings = picking_ids.read(fields_to_read)
            # pickings = picking_ids[0].read(fields_to_read)
        data_custom = self.get_suggestions_by_so(picking_ids)
        for picking in pickings:
            picking['move_line_ids'] = self.env['stock.move.line'].browse(picking.pop('move_line_ids')).read([
                'product_id',
                'location_id',
                'location_dest_id',
                'qty_done',
                'display_name',
                'product_uom_qty',
                'product_uom_id',
                'product_barcode',
                'owner_id',
                'lot_id',
                'lot_name',
                'package_id',
                'result_package_id',
                'dummy_id',
            ])

            # Prefetch data
            product_ids = tuple(set([move_line_id['product_id'][0] for move_line_id in picking['move_line_ids']]))
            tracking_and_barcode_per_product_id = {}
            for res in self.env['product.product'].with_context(active_test=False).search_read(
                    [('id', 'in', product_ids)], ['tracking', 'barcode']):
                tracking_and_barcode_per_product_id[res.pop("id")] = res

            for move_line_id in picking['move_line_ids']:
                id = move_line_id.pop('product_id')[0]
                move_line_id['product_id'] = {"id": id, **tracking_and_barcode_per_product_id[id]}
                id, name = move_line_id.pop('location_id')
                move_line_id['location_id'] = {"id": id, "display_name": name}
                id, name = move_line_id.pop('location_dest_id')
                move_line_id['location_dest_id'] = {"id": id, "display_name": name}
            id, name = picking.pop('location_id')
            picking['location_id'] = self.env['stock.location'].search_read([("id", "=", id)], [
                'parent_path'
            ])[0]
            picking['location_id'].update({"id": id, "display_name": name})
            id, name = picking.pop('location_dest_id')
            picking['location_dest_id'] = self.env['stock.location'].search_read([("id", "=", id)], [
                'parent_path'
            ])[0]
            picking['location_dest_id'].update({"id": id, "display_name": name})
            picking['group_stock_multi_locations'] = self.env.user.has_group('stock.group_stock_multi_locations')
            picking['group_tracking_owner'] = self.env.user.has_group('stock.group_tracking_owner')
            picking['group_tracking_lot'] = self.env.user.has_group('stock.group_tracking_lot')
            picking['group_production_lot'] = self.env.user.has_group('stock.group_production_lot')
            picking['group_uom'] = self.env.user.has_group('uom.group_uom')
            picking['use_create_lots'] = self.env['stock.picking.type'].browse(
                picking['picking_type_id'][0]).use_create_lots
            picking['use_existing_lots'] = self.env['stock.picking.type'].browse(
                picking['picking_type_id'][0]).use_existing_lots
            picking['show_entire_packs'] = self.env['stock.picking.type'].browse(
                picking['picking_type_id'][0]).show_entire_packs
            picking['actionReportDeliverySlipId'] = self.env.ref('stock.action_report_delivery').id
            picking['actionReportBarcodesZplId'] = self.env.ref('stock.action_label_transfer_template_zpl').id
            picking['actionReportBarcodesPdfId'] = self.env.ref('stock.action_label_transfer_template_pdf').id
            picking['actionReportMatriculaId'] = self.env.ref(
                'stock_barcode_custom.action_report_registration_order').id
            picking['actionReportBultoId'] = self.env.ref('stock_barcode_custom.action_report_package_sale_order').id
            if self.env.company.nomenclature_id:
                picking['nomenclature_id'] = [self.env.company.nomenclature_id.id]
            if data_custom:
                picking['suggestions_custom'] = data_custom
                picking['picking_ids'] = picking_ids[::-1].ids
            if sale.x_inventory_state:
                picking['state'] = sale.x_inventory_state
        return pickings

    def get_suggestions_by_so(self, picking_ids):
        result = {}
        for picking in picking_ids:
            result[picking.id] = []
            for line in picking.move_line_ids_without_package:
                if line.product_uom_qty - line.qty_done > 0:
                    real_qty = line.product_uom_qty - line.qty_done
                    res_line = {
                        'product_id': line.product_id.id,
                        'product_name': line.product_id.display_name,
                        'product_image': line.product_id.image_1920,
                        'product_description_picking': line.product_id.description_picking,
                        'product_x_manufacturer': line.product_id.x_manufacturer_code,
                        'uom_id': line.product_id.uom_id.id,
                        'location_id': line.location_id.id,
                        'location_name': line.location_id.display_name,
                        'qty': real_qty,
                    }
                    if line.result_package_id.id:
                        product_pack = self.env['product.packaging'].search([('product_id', '=', line.product_id.id),
                                                                             ('x_package', '=',
                                                                              line.result_package_id.id)],
                                                                            limit=1)
                        res_line['package_id'] = line.result_package_id.id
                        res_line['package_name'] = line.result_package_id.name
                        res_line['packages_count'] = res_line['qty'] / (product_pack.qty or 1)
                        res_line['pack_size'] = product_pack.qty

                    result[picking.id].append(res_line)
            if len(result[picking.id]) <= 0:
                del result[picking.id]
        return result

    def _get_picking_fields_to_read(self):
        """ Return the default fields to read from the picking.
        """
        return [
            'id',
            'move_line_ids',
            'picking_type_id',
            'location_id',
            'location_dest_id',
            'name',
            'state',
            'picking_type_code',
            'company_id',
            'origin',
        ]

    def get_po_to_split_from_barcode(self, barcode):
        """ Returns the lot wizard's action for the move line matching
        the barcode. This method is intended to be called by the
        `picking_barcode_handler` javascript widget when the user scans
        the barcode of a tracked product.
        """
        product_id = self.env['product.product'].search([('barcode', '=', barcode)])
        candidates = self.env['stock.move.line'].search([
            ('picking_id', 'in', self.ids),
            ('product_barcode', '=', barcode),
            ('location_processed', '=', False),
            ('result_package_id', '=', False),
        ])

        action_ctx = dict(self.env.context,
                          default_picking_id=self.id,
                          serial=self.product_id.tracking == 'serial',
                          default_product_id=product_id.id,
                          candidates=candidates.ids)
        view_id = self.env.ref('stock_barcode_custom.view_barcode_lot_form').id
        return {
            'name': _('Lot/Serial Number Details'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'stock_barcode.lot',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'context': action_ctx}

    def new_product_scanned(self, barcode):
        # TODO: remove this method in master, it's not used anymore
        product_id = self.env['product.product'].search([('barcode', '=', barcode)])
        if not product_id or product_id.tracking == 'none':
            return self.on_barcode_scanned(barcode)
        else:
            return self.get_po_to_split_from_barcode(barcode)

    def _check_product(self, product, qty=1.0):
        """ This method is called when the user scans a product. Its goal
        is to find a candidate move line (or create one, if necessary)
        and process it by incrementing its `qty_done` field with the
        `qty` parameter.
        """
        # Get back the move line to increase. If multiple are found, chose
        # arbitrary the first one. Filter out the ones processed by
        # `_check_location` and the ones already having a # destination
        # package.
        picking_move_lines = self.move_line_ids_without_package
        if not self.show_reserved:
            picking_move_lines = self.move_line_nosuggest_ids

        corresponding_ml = picking_move_lines.filtered(lambda
                                                           ml: ml.product_id.id == product.id and not ml.result_package_id and not ml.location_processed and not ml.lots_visible)[
                           :1]

        if corresponding_ml:
            corresponding_ml.qty_done += qty
        else:
            # If a candidate is not found, we create one here. If the move
            # line we add here is linked to a tracked product, we don't
            # set a `qty_done`: a next scan of this product will open the
            # lots wizard.
            picking_type_lots = (self.picking_type_id.use_create_lots or self.picking_type_id.use_existing_lots)
            new_move_line = self.move_line_ids.new({
                'product_id': product.id,
                'product_uom_id': product.uom_id.id,
                'location_id': self.location_id.id,
                'location_dest_id': self.location_dest_id.id,
                'qty_done': (product.tracking == 'none' and picking_type_lots) and qty or 0.0,
                'product_uom_qty': 0.0,
                'date': fields.datetime.now(),
            })
            if self.show_reserved:
                self.move_line_ids_without_package += new_move_line
            else:
                self.move_line_nosuggest_ids += new_move_line
        return True

    def _check_source_package(self, package):
        corresponding_po = self.move_line_ids.filtered(
            lambda r: r.package_id.id == package.id and r.result_package_id.id == package.id)
        for po in corresponding_po:
            po.qty_done = po.product_uom_qty
        if corresponding_po:
            self.entire_package_detail_ids.filtered(lambda p: p.name == package.name).is_processed = True
            return True
        else:
            return False

    def _check_destination_package(self, package):
        """ This method is called when the user scans a package currently
        located in (or in any of the children of) the destination location
        of the picking. Its goal is to set this package as a destination
        package for all the processed move lines not having a destination
        package.
        """
        corresponding_ml = self.move_line_ids.filtered(
            lambda ml: not ml.result_package_id and float_compare(ml.qty_done, 0,
                                                                  precision_rounding=ml.product_uom_id.rounding) == 1)
        # If the user processed the whole reservation (or more), simply
        # write the `package_id` field.
        # If the user processed less than the reservation, split the
        # concerned move line in two: one where the `package_id` field
        # is set with the processed quantity as `qty_done` and another
        # one with the initial values.
        for ml in corresponding_ml:
            rounding = ml.product_uom_id.rounding
            if float_compare(ml.qty_done, ml.product_uom_qty, precision_rounding=rounding) == -1:
                self.move_line_ids += self.move_line_ids.new({
                    'product_id': ml.product_id.id,
                    'package_id': ml.package_id.id,
                    'product_uom_id': ml.product_uom_id.id,
                    'location_id': ml.location_id.id,
                    'location_dest_id': ml.location_dest_id.id,
                    'qty_done': 0.0,
                    'move_id': ml.move_id.id,
                    'date': fields.datetime.now(),
                })
            ml.result_package_id = package.id
        return True

    def _check_destination_location(self, location):
        """ This method is called when the user scans a location. Its goal
        is to find the move lines previously processed and write the scanned
        location as their `location_dest_id` field.
        """
        # Get back the move lines the user processed. Filter out the ones where
        # this method was already applied thanks to `location_processed`.
        corresponding_ml = self.move_line_ids.filtered(
            lambda ml: not ml.location_processed and float_compare(ml.qty_done, 0,
                                                                   precision_rounding=ml.product_uom_id.rounding) == 1)

        # If the user processed the whole reservation (or more), simply
        # write the `location_dest_id` and `location_processed` fields
        # on the concerned move line.
        # If the user processed less than the reservation, split the
        # concerned move line in two: one where the `location_dest_id`
        # and `location_processed` fields are set with the processed
        # quantity as `qty_done` and another one with the initial values.
        for ml in corresponding_ml:
            rounding = ml.product_uom_id.rounding
            if float_compare(ml.qty_done, ml.product_uom_qty, precision_rounding=rounding) == -1:
                self.move_line_ids += self.move_line_ids.new({
                    'product_id': ml.product_id.id,
                    'package_id': ml.package_id.id,
                    'product_uom_id': ml.product_uom_id.id,
                    'location_id': ml.location_id.id,
                    'location_dest_id': ml.location_dest_id.id,
                    'qty_done': 0.0,
                    'move_id': ml.move_id.id,
                    'date': fields.datetime.now(),
                })
            ml.update({
                'location_processed': True,
                'location_dest_id': location.id,
            })
        return True

    def on_barcode_scanned(self, barcode):
        if not self.env.company.nomenclature_id:
            # Logic for products
            product = self.env['product.product'].search(
                ['|', ('barcode', '=', barcode), ('default_code', '=', barcode)], limit=1)
            if product:
                if self._check_product(product):
                    return

            product_packaging = self.env['product.packaging'].search([('barcode', '=', barcode)], limit=1)
            if product_packaging.product_id:
                if self._check_product(product_packaging.product_id, product_packaging.qty):
                    return

            # Logic for packages in source location
            if self.move_line_ids:
                package_source = self.env['stock.quant.package'].search(
                    [('name', '=', barcode), ('location_id', 'child_of', self.location_id.id)], limit=1)
                if package_source:
                    if self._check_source_package(package_source):
                        return

            # Logic for packages in destination location
            package = self.env['stock.quant.package'].search([('name', '=', barcode), '|', ('location_id', '=', False),
                                                              ('location_id', 'child_of', self.location_dest_id.id)],
                                                             limit=1)
            if package:
                if self._check_destination_package(package):
                    return

            # Logic only for destination location
            location = self.env['stock.location'].search(['|', ('name', '=', barcode), ('barcode', '=', barcode)],
                                                         limit=1)
            if location and location.search_count(
                    [('id', '=', location.id), ('id', 'child_of', self.location_dest_id.ids)]):
                if self._check_destination_location(location):
                    return
        else:
            parsed_result = self.env.company.nomenclature_id.parse_barcode(barcode)
            if parsed_result['type'] in ['weight', 'product']:
                if parsed_result['type'] == 'weight':
                    product_barcode = parsed_result['base_code']
                    qty = parsed_result['value']
                else:  # product
                    product_barcode = parsed_result['code']
                    qty = 1.0
                product = self.env['product.product'].search(
                    ['|', ('barcode', '=', product_barcode), ('default_code', '=', product_barcode)], limit=1)
                if product:
                    if self._check_product(product, qty):
                        return

            if parsed_result['type'] == 'package':
                if self.move_line_ids:
                    package_source = self.env['stock.quant.package'].search(
                        [('name', '=', parsed_result['code']), ('location_id', 'child_of', self.location_id.id)],
                        limit=1)
                    if package_source:
                        if self._check_source_package(package_source):
                            return
                package = self.env['stock.quant.package'].search(
                    [('name', '=', parsed_result['code']), '|', ('location_id', '=', False),
                     ('location_id', 'child_of', self.location_dest_id.id)], limit=1)
                if package:
                    if self._check_destination_package(package):
                        return

            if parsed_result['type'] == 'location':
                location = self.env['stock.location'].search(
                    ['|', ('name', '=', parsed_result['code']), ('barcode', '=', parsed_result['code'])], limit=1)
                if location and location.search_count(
                        [('id', '=', location.id), ('id', 'child_of', self.location_dest_id.ids)]):
                    if self._check_destination_location(location):
                        return

            product_packaging = self.env['product.packaging'].search([('barcode', '=', parsed_result['code'])], limit=1)
            if product_packaging.product_id:
                if self._check_product(product_packaging.product_id, product_packaging.qty):
                    return

        return {'warning': {
            'title': _('Wrong barcode'),
            'message': _('The barcode "%(barcode)s" doesn\'t correspond to a proper product, package or location.') % {
                'barcode': barcode}
        }}

    def open_picking(self):
        """ method to open the form view of the current record
        from a button on the kanban view
        """
        self.ensure_one()
        view_id = self.env.ref('stock.view_picking_form').id
        return {
            'name': _('Open picking form'),
            'res_model': 'stock.picking',
            'view_mode': 'form',
            'view_id': view_id,
            'type': 'ir.actions.act_window',
            'res_id': self.id,
        }

    def open_picking_client_action(self):
        """ method to open the form view of the current record
        from a button on the kanban view
        """
        self.ensure_one()
        use_form_handler = self.env['ir.config_parameter'].sudo().get_param('stock_barcode_custom.use_form_handler')
        if use_form_handler:
            view_id = self.env.ref('stock.view_picking_form').id
            return {
                'name': _('Open picking form'),
                'res_model': 'stock.picking',
                'view_mode': 'form',
                'view_id': view_id,
                'type': 'ir.actions.act_window',
                'res_id': self.id,
            }
        else:
            action = self.env.ref('stock_barcode_custom.stock_barcode_picking_client_action').read()[0]
            params = {
                'model': 'stock.picking',
                'picking_id': self.id,
                'nomenclature_id': [self.env.company.nomenclature_id.id],
            }
            return dict(action, target='fullscreen', params=params)

    # package-barcode-so-custom

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
                                                            float_compare(ml.qty_done, 0.0,
                                                                          precision_rounding=ml.product_uom_id.rounding) > 0
                                                            and not ml.x_package_processed
                                                            )
            else:
                move_line_ids = picking_move_lines.filtered(lambda ml:
                                                            float_compare(ml.qty_done, 0.0,
                                                                          precision_rounding=ml.product_uom_id.rounding) > 0
                                                            and not ml.result_package_id
                                                            )

            if not move_line_ids:
                move_line_ids = picking_move_lines.filtered(lambda ml: float_compare(ml.product_uom_qty, 0.0,
                                                                                     precision_rounding=ml.product_uom_id.rounding) > 0 and float_compare(
                    ml.qty_done, 0.0,
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

            sequence = self.env.ref("stock_barcode_custom.seq_x_package_barcode_so_custom")
            name = sequence and sequence.next_by_id() or '/'

            package = False
            for pick in self:
                move_lines_to_pack = self.env['stock.move.line']
                package = self.env['stock.quant.package'].create({'name': name})

                precision_digits = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                if float_is_zero(move_line_ids[0].qty_done, precision_digits=precision_digits):
                    for line in move_line_ids:
                        line.qty_done = line.product_uom_qty

                for ml in move_line_ids:
                    if float_compare(ml.qty_done, ml.product_uom_qty,
                                     precision_rounding=ml.product_uom_id.rounding) >= 0:
                        move_lines_to_pack |= ml
                    else:
                        quantity_left_todo = float_round(ml.product_uom_qty - ml.qty_done,
                                                         precision_rounding=ml.product_uom_id.rounding,
                                                         rounding_method='UP')
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
            return super(StockPicking, self)._put_in_pack(move_line_ids)

    def get_packaging_report_packaging(self):
        toreturn = list()

        # Get Company Logo
        company = self.env['res.company'].search([], order="id asc")

        for record in self:
            for line in record.move_line_ids_without_package or []:
                if line.result_package_id:
                    data_find = list(data for data in toreturn if data['package_id'] == line.result_package_id.id)
                    if not data_find:
                        qty = line.qty_done if line.state == 'done' else line.product_uom_qty
                        toreturn.append({
                            'is_tss': record.partner_id.x_is_tss,
                            'company_id': company[1].id if record.partner_id.x_is_tss else company[0].id,
                            'company_name': company[1].name if record.partner_id.x_is_tss else company[0].name,
                            'company_vat': company[1].vat if record.partner_id.x_is_tss else company[0].vat,

                            'company': company[1].partner_id if record.partner_id.x_is_tss else company[0].partner_id,
                            'partner': record.partner_id,

                            'carrier_name': record.carrier_id.name,
                            'weight': float(line.product_id.weight * qty),
                            'weight_uom_name': line.product_id.weight_uom_name,

                            'package_id': line.result_package_id.id,
                            'package_name': line.result_package_id.name,
                            'sale_name': record.sale_id.name if record.sale_id else '',
                            'picking_name': record.name,
                        })
                    else:
                        data_find[0]['weight'] = float(data_find[0]['weight']) + (line.product_id.weight * qty)

        return toreturn

    # product packaging custom

    def has_origin(self):
        return True if self.origin else False

class StockPickingType(models.Model):

    _inherit = 'stock.picking.type'

    def get_action_picking_tree_ready_kanban(self):
        return self._get_action('stock_barcode_custom.stock_picking_action_kanban')
