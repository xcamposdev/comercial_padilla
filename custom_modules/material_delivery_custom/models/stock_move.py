
import logging
#from server.odoo.fields import Float

from odoo import api, fields, models, tools
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class material_delivery_stock_move(models.Model):

    _inherit = "stock.move"

    x_packaging = fields.Many2one('stock.quant.package', string="Paquete")
