from odoo import api, models, fields
from odoo.addons.sale.models.sale import SaleOrder as Sale


class SaleOrderCustom(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _default_shipping_type(self):
        warehouse_id = self.env['ir.config_parameter'].sudo().get_param('sale_location_default_custom.x_warehouse_id') or False
        if warehouse_id:
            return int(warehouse_id)
        return super(SaleOrderCustom, self)._default_shipping_type()

    warehouse_id = fields.Many2one('stock.warehouse', 'Shipping To',
                                      required=True, default=_default_shipping_type, 
                                      domain="[('company_id', '=', company_id)]",
                                      help="This will determine operation type of incoming shipment")
