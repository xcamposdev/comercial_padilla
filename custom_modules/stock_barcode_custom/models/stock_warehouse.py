from odoo import fields, models


class StockWarehouse(models.Model):

    _inherit = "stock.warehouse"

    x_auto_re_stock = fields.Boolean(string="Movimientos de re-abastecimiento automatico", default=False)
