from itertools import groupby
import logging
import threading
from odoo import fields, models, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrderStockBacode(models.Model):
    
    _inherit = "sale.order"

    x_partner_id_x_is_tss = fields.Boolean(string='¿Es TSS?', compute="_compute_get_partner_x_is_tss")
    x_picking_count = fields.Integer(string='Nro of picks', compute='_compute_number_picks')
    x_item_count = fields.Integer(string='Nro of items', compute='_compute_number_items')
    x_unit_total = fields.Integer(string='Nro of units', compute='_compute_number_units')
    x_weight_total = fields.Float(string="Weight total", compute="_compute_weight_total")
    x_weight_total_uom = fields.Char(string="Weight Uom", compute="_compute_weight_total_uom")

    def _compute_get_partner_x_is_tss(self):
        for record in self:
            record.x_partner_id_x_is_tss = record.partner_id.x_is_tss

    @api.depends('picking_ids')
    def _compute_number_picks(self):
        for order in self:
            if order.warehouse_id:
                picks = list(data for data in order.picking_ids if data.picking_type_id in (order.warehouse_id.pick_type_id, order.warehouse_id.int_type_id))
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

    def _compute_weight_total_uom(self):
        for order in self:
            weight = ""
            for data in order.order_line:
                if data.product_id:
                    weight = data.product_id.weight_uom_name
                    break
            order.x_weight_total_uom = weight

    def open_picking_client_action(self):
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
            picking_ids = list(data.id for data in self.picking_ids \
                                            if data.picking_type_id.id == self.warehouse_id.pick_type_id.id or data.picking_type_id.id == self.warehouse_id.int_type_id.id)
            data_custom = self.get_suggestions_by_id(self.id)
            action = self.env.ref('stock_barcode_custom.stock_barcode_picking_client_action_custom').read()[0]
            params = {
                'suggestions_custom': data_custom,
                'model': 'stock.picking',
                'picking_id': picking_ids,#self.id,
                'nomenclature_id': [self.env.company.nomenclature_id.id],
            }
            return dict(action, target='fullscreen', params=params)

    @staticmethod
    def group_by_field(data, group_by):
        # This method group a list by a key in dict
        res = {}
        for k, v in groupby(data, key=lambda x: x[group_by]):
            key = k[0] if type(k) is tuple else k
            if key in res:
                res[key] += list(v)
            else:
                res[key] = list(v)
        return res

    def products_pick_finder(self, lines, **kwargs) -> tuple:
        # This method find the availables stock quants availables to complete a SO.
        # returns a tuple

        group_by = kwargs['group_by'] if 'group_by' in kwargs else 'location_id'
        products = {p.product_id.id: {'qty': p.product_uom_qty, 'product': p.product_id} for p in lines}
        location_domain = []
        second_level_suggested_lines = []
        result = []
        # resupply_products = []
        quant_domain = [('product_id', 'in', list(products.keys())),
                        ('quantity', '>', 0)]
        stock_quantity = self.env['stock.quant']
        if 'location_domain' in kwargs:
            location_domain = kwargs['location_domain']

        stock_quantity_list = stock_quantity.search_read(quant_domain + location_domain,
                                                         ['product_id', 'location_id', 'quantity',
                                                          'reserved_quantity',
                                                          'inventory_quantity', 'package_id'],
                                                         order='package_id asc')
        packaging_ids = {p['x_package'][0]: p for p in
                         self.env['product.packaging'].search_read([('product_id', 'in', list(products.keys()))],
                                                                   ['id', 'x_package', 'product_id', 'x_location',
                                                                    'qty'],
                                                                   order='qty desc') if p['x_package']}
        for p in stock_quantity_list:
            available_qty = p['quantity'] - p['reserved_quantity']
            requested_qty = products[p['product_id'][0]]['qty']
            if products[p['product_id'][0]]['qty'] > 0:
                uom_id = products[p['product_id'][0]]['product'].uom_id.id
                if p['package_id']:
                    if p['package_id'][0] in packaging_ids and not packaging_ids[p['package_id'][0]]['x_location']:
                        raise UserError(
                            'El empaquetado "%s" no tiene asignado una ubicación para el producto "%s"' % (
                                p['package_id'][1], p['product_id'][1]))
                    packs_requested = SaleOrderStockBacode._get_available_per_pack(
                        requested_qty, available_qty, packaging_ids[p['package_id'][0]]['qty'])
                    if packs_requested > 0:
                        result.append({
                            'product_id': p['product_id'],
                            'uom_id': uom_id,
                            'package_id': p['package_id'],
                            'location_id': packaging_ids[p['package_id'][0]]['x_location'][0],
                            'qty': packs_requested,
                            'packages_count': packs_requested / packaging_ids[p['package_id'][0]]['qty'],
                            'pack_size': packaging_ids[p['package_id'][0]]['qty'],
                        })
                        products[p['product_id'][0]]['qty'] -= packs_requested
                        if available_qty - packs_requested > 0:
                            second_level_suggested_lines.append({
                                'product_id': p['product_id'],
                                'uom_id': uom_id,
                                'package_id': False,
                                'location_id': packaging_ids[p['package_id'][0]]['x_location'][0],
                                'available_qty': available_qty - packs_requested,
                            })
                    elif available_qty > 0:
                        second_level_suggested_lines.append({
                            'product_id': p['product_id'],
                            'uom_id': uom_id,
                            'package_id': False,
                            'location_id': packaging_ids[p['package_id'][0]]['x_location'][0],
                            'available_qty': available_qty,
                        })
                elif available_qty > 0:
                    qty = requested_qty if available_qty > requested_qty else available_qty
                    result.append({
                        'product_id': p['product_id'],
                        'uom_id': uom_id,
                        'package_id': p['package_id'],
                        'location_id': p['location_id'][0],
                        'qty': qty,
                    })
                    products[p['product_id'][0]]['qty'] -= qty

        products_missed = [key for key, val in products.items() if val['qty'] > 0]

        if len(products_missed) > 0:
            packages_to_unit = SaleOrderStockBacode.group_by_field(second_level_suggested_lines, 'product_id')
            for p_id in products_missed:
                if p_id in packages_to_unit and products[p_id]['qty'] > 0:
                    p_ref = packages_to_unit[p_id]
                    for p in p_ref:
                        requested_qty = products[p_id]['qty']
                        qty = requested_qty if p['available_qty'] > requested_qty else p['available_qty']
                        p['qty'] = qty
                        result.append(p)
                        products[p_id]['qty'] -= qty
                # elif products[p_id]['qty'] > 0:
                #     packs_to_suppy = self.env['product.packaging'].search([('product_id', '=', p_id)], order='qty desc')
                #     for pack in packs_to_suppy:
                #         qty_required = SaleOrderStockBacode._get_available_per_pack(
                #             products[p_id]['qty'], 1000000, pack.qty)
                #         resupply_products.append({
                #                 'product_id': p_id,
                #                 'uom_id': pack.product_id.uom_id.id,
                #                 'package_id': pack.id,
                #                 'location_id': pack.x_location.id,
                #                 'qty': qty_required,
                #                 're_supply': True,
                #         })
                #         products[p_id]['qty'] -= qty_required

        products_missed = [key for key, val in products.items() if val['qty'] > 0]

        if len(products_missed) > 0:
            _logger.debug("Called: {} products that are not available: {}".format('products_pick_finder', products_missed))
        _logger.debug("Called: {} and the sugested lines generated: {}".format('products_pick_finder', result))
        return SaleOrderStockBacode.group_by_field(result, group_by), products_missed

    def get_suggestions_by_id(self, sale_order_id):
        sale_order = self.search([('id', '=', int(sale_order_id))])
        return self.products_pick_finder(sale_order.order_line)

    def action_confirm(self):
        """ This method extends the actual behavior adding an automatic option to create
        stock moves to restock the quantity needed.

        :return: bool
        """
        sale = super(SaleOrderStockBacode, self).action_confirm()

        if self.warehouse_id.delivery_steps != 'pick_pack_ship' and not self.warehouse_id.x_auto_re_stock:
            return sale

        # TODO: change this when this client manage only one virtual warehouse like in the real world is
        picking_type_id = self.env['ir.config_parameter'].sudo().get_param('purchase_location_default_custom'
                                                                           '.x_picking_type_id') or False

        stock_id = self.warehouse_id.lot_stock_id.id
        root_ids = [self.warehouse_id.lot_stock_id.x_root_location_id]
        if picking_type_id:
            picking_type = self.env['stock.picking.type'].search([('id', '=', picking_type_id)], limit=1)
            root_ids.append(picking_type.warehouse_id.view_location_id.id)
        custom_domain = [('location_id.x_root_location_id', 'in', root_ids)]

        lines_to_compute, missed_products = self.products_pick_finder(self.order_line, location_domain=custom_domain)

        if len(missed_products) > 0:
            ssc = self.env['stock.scheduler.compute']
            threaded_calculation = threading.Thread(target=ssc._procure_calculation_orderpoint, args=())
            threaded_calculation.start()

        move_ref = self.env['stock.move'].search([
            ('product_id', '=', self.order_line.move_ids[0].product_id.id),
            ('origin', '=', self.order_line.move_ids[0].origin)], limit=1)

        for location_id, move_lines in lines_to_compute.items():
            if location_id != stock_id:
                picking_id = self.create_stock_piking_material_delivery(move_ref, location_id, stock_id)
                for m_line in move_lines:
                    if m_line['package_id']:
                        self._generate_move_lines(move_ref, picking_id, m_line['product_id'][1], m_line['product_id'][0],
                                                  m_line['uom_id'], m_line['qty'],
                                                  location_id, stock_id, m_line['package_id'][0])
                    else:
                        self._generate_move_lines(move_ref, picking_id, m_line['product_id'][1], m_line['product_id'][0],
                                                  m_line['uom_id'], m_line['qty'],
                                                  location_id, stock_id)

                picking_id.action_confirm()
                picking_id.action_assign()

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

    def _generate_move_lines(self, last_move, picking_id, p_display_name, product_id, p_uom_id, quantity, location_id,
                             location_dest_id,
                             packaging_id=None, package_level=None):
        move = self.env['stock.move'].sudo().create({
            'picking_id': picking_id.id,
            'name': p_display_name,
            'product_id': product_id,
            'product_uom_qty': quantity,
            'product_uom': p_uom_id,
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
            'picking_type_id': self.warehouse_id.int_type_id.id,
            'location_id': location_id,
            'location_dest_id': dest_location_id,
            'scheduled_date': last_move.date,
            'origin': last_move.origin,
            'sale_id': self.id,
            'group_id': last_move.group_id.id,
        }
        res = self.env['stock.picking'].create(stock_picking_values)
        return res
