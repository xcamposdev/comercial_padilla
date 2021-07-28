# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):

    _inherit = 'res.partner'

    x_is_tss = fields.Boolean(string='PADILLA/TSS')
