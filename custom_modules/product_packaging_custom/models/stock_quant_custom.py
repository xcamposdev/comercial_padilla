# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from psycopg2 import OperationalError, Error

class Stock_Quant_Custom(models.Model):

    _inherit = 'stock.quant'

    x_packaging_id = fields.Many2one('product.packaging', string='Empaquetado del Producto')
    x_packaging_qty = fields.Float(string='Cantidad')
    x_units_format = fields.Float(string="Unidades (formato)", compute="_compute_x_units_format")
    
    def _compute_x_units_format(self):
        for record in self:
            record.x_units_format = (record.x_packaging_qty or 0) / (record.inventory_quantity if record.inventory_quantity != 0 else 1)

    @api.model
    def _update_available_quantity_custom(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, in_date=None, packaging_id=None, packaging_qty=None):
        """ Increase or decrease `reserved_quantity` of a set of quants for a given set of
        product_id/location_id/lot_id/package_id/owner_id.

        :param product_id:
        :param location_id:
        :param quantity:
        :param lot_id:
        :param package_id:
        :param owner_id:
        :param datetime in_date: Should only be passed when calls to this method are done in
                                 order to move a quant. When creating a tracked quant, the
                                 current datetime will be used.
        :return: tuple (available_quantity, in_date as a datetime)
        """
        self = self.sudo()
        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)

        incoming_dates = [d for d in quants.mapped('in_date') if d]
        incoming_dates = [fields.Datetime.from_string(incoming_date) for incoming_date in incoming_dates]
        if in_date:
            incoming_dates += [in_date]
        # If multiple incoming dates are available for a given lot_id/package_id/owner_id, we
        # consider only the oldest one as being relevant.
        if incoming_dates:
            in_date = fields.Datetime.to_string(min(incoming_dates))
        else:
            in_date = fields.Datetime.now()

        for quant in quants:
            try:
                with self._cr.savepoint():
                    self._cr.execute("SELECT 1 FROM stock_quant WHERE id = %s FOR UPDATE NOWAIT", [quant.id], log_exceptions=False)
                    quant.write({
                        'x_packaging_id': (packaging_id.id if packaging_id else False),
                        'x_packaging_qty': (packaging_qty if packaging_qty else False),
                    })
                    break
            except OperationalError as e:
                if e.pgcode == '55P03':  # could not obtain the lock
                    continue
                else:
                    raise
        return self._get_available_quantity(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=False, allow_negative=True), fields.Datetime.from_string(in_date)