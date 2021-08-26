# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class ResPartnerDiscount(models.Model):
    
    _inherit = "res.partner"

    x_purchase_discount = fields.Float(string="Descuento Global (%)", default=0)
