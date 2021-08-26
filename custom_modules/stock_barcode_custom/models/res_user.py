from odoo import fields, models


class ResUserCustom(models.Model):

    _inherit = "res.users"

    x_pick = fields.Boolean(string='PICK', default=True)
    x_pack = fields.Boolean(string='PACK', default=True)
    x_out = fields.Boolean(string='OUT', default=True)
