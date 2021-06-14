
import logging
#from server.odoo.fields import Float

from odoo import api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class material_delivery_stock_move(models.Model):

    _inherit = "stock.move"

    x_packaging = fields.Many2one('stock.quant.package', string="Paquete")

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        vals = super(material_delivery_stock_move, self)._prepare_move_line_vals()
        if self.x_packaging and reserved_quant and self.x_packaging == reserved_quant.package_id:
            vals['package_id'] = self.x_packaging.id
            vals['result_package_id'] = self.x_packaging.id
        return vals