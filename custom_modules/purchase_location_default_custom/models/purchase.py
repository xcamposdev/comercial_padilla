from odoo import api, models, fields
from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase


class PurchaseOrderCustom(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def _default_picking_type(self):
        picking_type_id = self.env['ir.config_parameter'].sudo().get_param('purchase_location_default_custom'
                                                                           '.x_picking_type_id') or False
        if picking_type_id:
            return int(picking_type_id)
        return super(PurchaseOrderCustom, self)._default_picking_type()

    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', states=Purchase.READONLY_STATES,
                                      required=True, default=_default_picking_type,
                                      domain="['|', ('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id)]",
                                      help="This will determine operation type of incoming shipment")
