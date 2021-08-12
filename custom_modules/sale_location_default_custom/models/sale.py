from odoo import api, models, fields
from odoo.addons.sale.models.sale import SaleOrder as Sale


class SaleOrderCustom(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _default_warehouse_id(self):
        warehouse_id = self.env['ir.config_parameter'].sudo().get_param('sale_location_default_custom.x_warehouse_id') or False
        
        if warehouse_id:
            return int(warehouse_id)
        return super(SaleOrderCustom, self)._default_warehouse_id()

    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse', required=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        default=_default_warehouse_id, check_company=True)

