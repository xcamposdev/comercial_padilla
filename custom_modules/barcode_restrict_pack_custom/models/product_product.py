# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models, api


class ProductCustom(models.Model):

    _inherit = 'product.product'

    @api.model
    def get_all_products_by_barcode(self, context=None):
        if context is None:
            context = {}
        product_domain = [('barcode', '!=', None), ('type', '!=', 'service')]
        packagin_domain = [('barcode', '!=', None), ('product_id', '!=', None)]
        if 'pickingId' in context.keys():
            picking_id = self.env['stock.picking'].search([('id', '=', context['pickingId'])])
            # Check if the movement is pick to pack
            if picking_id.origin and picking_id.sale_id and picking_id.picking_type_id and \
                    picking_id.sale_id.warehouse_id.pick_type_id.id == picking_id.picking_type_id.id:
                product_ids = list(set(operations.product_id.id for operations in picking_id.move_ids_without_package))
                product_domain.append(('id', 'in', product_ids))
                packagin_domain.append(('product_id.id', 'in', product_ids))

        products = self.env['product.product'].search_read(
            product_domain,
            ['barcode', 'display_name', 'uom_id', 'tracking']
        )
        packagings = self.env['product.packaging'].search_read(
            packagin_domain,
            ['id','barcode', 'product_id', 'qty','x_package','x_location']
        )
        # for each packaging, grab the corresponding product data
        to_add = []
        to_read = []
        products_by_id = {product['id']: product for product in products}
        for packaging in packagings:
            
            packaging['packaging_id'] = packaging['id'];
            if packaging.get('x_location', False):
                stock_location = self.env['stock.location'].search([('id','=',packaging['x_location'][0])])
                packaging['x_location_barcode'] = stock_location.barcode

            if products_by_id.get(packaging['product_id']):
                product = products_by_id[packaging['product_id']]
                to_add.append(dict(product, **{'qty': packaging['qty']}))
            # if the product doesn't have a barcode, you need to read it directly in the DB
            to_read.append((packaging, packaging['product_id'][0]))
        products_to_read = self.env['product.product'].browse(list(set(t[1] for t in to_read))).sudo().read(['display_name', 'uom_id', 'tracking'])
        products_to_read = {product['id']: product for product in products_to_read}
        to_add.extend([dict(t[0], **products_to_read[t[1]]) for t in to_read])
        return {product.pop('barcode'): product for product in products + to_add}
