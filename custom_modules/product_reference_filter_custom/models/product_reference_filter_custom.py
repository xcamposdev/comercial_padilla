# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductReferenceFilterCustom(models.Model):

    _inherit = 'product.template'
    x_product_default_code = fields.Many2one('product.template', 'Sector', readonly=True)
