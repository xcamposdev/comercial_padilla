# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api


class Partner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    def _compute_product_pricelist(self):
        company = self.env.context.get('force_company', False)
        if not company:
            company = self.env['res.company'].search([], order='id asc', limit=1).id
            self.env.context = dict(self.env.context)
            self.env.context.update({'force_company': company})
        return super(Partner, self)._compute_product_pricelist()
