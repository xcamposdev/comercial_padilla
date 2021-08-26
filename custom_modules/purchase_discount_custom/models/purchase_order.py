# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

class PurchaseOrderDiscount(models.Model):
    
    _inherit = "purchase.order"

    x_global_discount = fields.Float("Descuento Global (%)", default=0)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super(PurchaseOrderDiscount, self).onchange_partner_id()
        self.x_global_discount = self.partner_id.x_purchase_discount

    @api.depends('order_line.price_total','x_global_discount')
    def _amount_all(self):
        for order in self:
            desc = (order.x_global_discount or 0.0)/100
            price_tax = price_total = price_subtotal = 0
            for line in order.order_line:
                price = (line.price_unit * (1 - (line.discount or 0.0) / 100.0)) * (1 - desc)
                taxes = line.taxes_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_id)
                price_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                price_total += taxes['total_included']
                price_subtotal += taxes['total_excluded']
            order.update({
                'amount_untaxed': price_subtotal,
                'amount_tax': price_tax,
                'amount_total': price_subtotal + price_tax,
            })

    def action_view_invoice(self):
        data = super(PurchaseOrderDiscount, self).action_view_invoice()
        data['context']['default_x_discount_global'] = self.x_global_discount
        return data


class PurchaseOrderLineDiscount(models.Model):
    
    _inherit = 'purchase.order.line'

    def _prepare_account_move_line(self, move):
        vals = super(PurchaseOrderLineDiscount, self)._prepare_account_move_line(move)
        vals["discount"] = self.discount
        return vals

    @api.onchange("product_qty", "product_uom")
    def _onchange_quantity(self):
        res = super()._onchange_quantity()
        if self.order_id.partner_id:
            self.discount = self.order_id.partner_id.default_supplierinfo_discount
        return res
