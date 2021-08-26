# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # TODO: Add translations
    x_picking_type_id = fields.Many2one('stock.picking.type', 'Recibir a',
                                        domain="['|', ('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id)]",
                                        help="Esto determinara donde se recibira el producto por defecto.")

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('purchase_location_default_custom.x_picking_type_id', self.x_picking_type_id.id)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        conf_param = self.env['ir.config_parameter'].sudo()
        picking_type_id = conf_param.get_param('purchase_location_default_custom.x_picking_type_id')
        res.update(
            x_picking_type_id=int(picking_type_id),
        )
        return res
