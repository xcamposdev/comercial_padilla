from odoo import api, models, fields


class SaleOrderCustom(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _default_warehouse_id(self):
        warehouse_id = self.env['ir.config_parameter'].sudo().get_param('sale_location_default_custom.x_warehouse_id') or False
        if warehouse_id:
            warehouse_ids = self.env['stock.warehouse'].search([('id', '=', int(warehouse_id))], limit=1)
            return warehouse_ids
        return super(SaleOrderCustom, self)._default_warehouse_id()

    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string="Default Warehouse",
        readonly=True,
        default=_default_warehouse_id,
        states={"draft": [("readonly", False)], "sent": [("readonly", False)]},
        help="If no source warehouse is selected on line, "
             "this warehouse is used as default.",
    )

    @api.onchange('company_id')
    def _onchange_company_id(self):
        warehouse_id = self.env['ir.config_parameter'].sudo().get_param(
            'sale_location_default_custom.x_warehouse_id') or False
        if warehouse_id:
            warehouse_ids = self.env['stock.warehouse'].search([('id', '=', int(warehouse_id))], limit=1)
            self.warehouse_id = warehouse_ids
        else:
            super(SaleOrderCustom, self)._onchange_company_id()
