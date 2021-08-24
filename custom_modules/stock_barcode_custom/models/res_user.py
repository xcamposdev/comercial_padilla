from odoo import fields, models


class ResUserCustom(models.Model):

    _inherit = "res.users"

    x_pick = fields.Boolean(string='PICK')
    x_pack = fields.Boolean(string='PACK')
    x_out = fields.Boolean(string='OUT')
