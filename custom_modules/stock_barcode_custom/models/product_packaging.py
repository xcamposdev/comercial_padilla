import logging

from odoo import fields, models, api
from datetime import datetime

_logger = logging.getLogger(__name__)


class Product_Packaging_Custom(models.Model):

    _inherit = "product.packaging"

    x_package = fields.Many2one('stock.quant.package', string="Paquete")
    x_location = fields.Many2one(related="x_package.location_id", relation='stock.location', string="Ubicación")


class QuantPackage_Custom(models.Model):

    _inherit = "stock.quant.package"

    location_id = fields.Many2one('stock.location', 'Location', compute='_compute_package_info', index=True, readonly=False, store=True)

    @api.depends('quant_ids.package_id', 'quant_ids.location_id', 'quant_ids.company_id', 'quant_ids.owner_id', 'quant_ids.quantity', 'quant_ids.reserved_quantity')
    def _compute_package_info(self):
        for package in self:
            values = {'location_id': False, 'owner_id': False}
            if package.quant_ids:
                values['location_id'] = package.quant_ids[0].location_id
                if all(q.owner_id == package.quant_ids[0].owner_id for q in package.quant_ids):
                    values['owner_id'] = package.quant_ids[0].owner_id
                if all(q.company_id == package.quant_ids[0].company_id for q in package.quant_ids):
                    values['company_id'] = package.quant_ids[0].company_id
            
            #####################################
            if not package.location_id:
                package.location_id = values['location_id']
            #####################################
            #package.location_id = values['location_id']
            package.company_id = values.get('company_id')
            package.owner_id = values['owner_id']
