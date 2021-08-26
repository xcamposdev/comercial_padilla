# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):

    _inherit = 'res.company'

    x_is_tss = fields.Boolean(string='¿Es TSS?')
