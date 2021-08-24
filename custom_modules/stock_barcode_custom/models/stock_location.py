# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, api, fields


class Location(models.Model):
    _inherit = 'stock.location'

    @api.model
    def get_all_locations_by_barcode(self):
        locations = self.env['stock.location'].search_read(
            [('barcode', '!=', None)], ['display_name', 'barcode', 'parent_path'])
        locationsByBarcode = {location.pop('barcode'): location for location in locations}
        return locationsByBarcode

    @api.depends('parent_path')
    def get_root_location_id(self):
        self.x_root_location_id = 0
        for location in self:
            if location.x_root_location_id:
                continue
            path_list = list(self.parent_path.split('/')[:-1])
            location.x_root_location_id = int(path_list[1]) if len(path_list) > 1 else int(path_list[0])

    def pro_search(self, operator, value):
        # TODO: this method only works with 'in' operator
        def custom_filter(location):
            if location.parent_path:
                path_res = list(location.parent_path.split('/')[:-1])
                if len(path_res) > 1 and int(path_res[1]) in value:
                    return True
                else:
                    if int(location.parent_path.split('/')[0]) in value:
                        return True
            return False
        recs = self.search([]).filtered(custom_filter)
        return [('id', operator, [x.id for x in recs] if recs else False)]

    x_root_location_id = fields.Integer(compute=get_root_location_id, search=pro_search)
