# -*- coding: utf-8 -*-
from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # TODO: Add translations
    x_warehouse_id = fields.Many2one('stock.warehouse', 'Entregas - almacen',
                                        domain="['|', ('id', '=', False), ('company_id', '=', company_id)]",
                                        help="Esto determinara donde se entregara el producto por defecto.")

    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param('sale_location_default_custom.x_warehouse_id', self.x_warehouse_id.id)
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        conf_param = self.env['ir.config_parameter'].sudo()
        house_id = conf_param.get_param('sale_location_default_custom.x_warehouse_id')
        res.update(
            x_warehouse_id = int(house_id),
        )
        return res
