from odoo import _, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _petmart_min_order_amount(self):
        return float(self.env['ir.config_parameter'].sudo().get_param('petmart.min_order_amount', 0))

    def _petmart_min_order_ok(self):
        self.ensure_one()
        return self.amount_untaxed >= self._petmart_min_order_amount()

    def action_confirm(self):
        # hard server-side enforcement, on top of the cart/checkout redirect
        for order in self.filtered('website_id'):
            minimum = order._petmart_min_order_amount()
            if minimum and order.amount_untaxed < minimum:
                raise UserError(_(
                    "The minimum order value is %(min)s. This order is %(amount)s.",
                    min=order.currency_id.format(minimum),
                    amount=order.currency_id.format(order.amount_untaxed),
                ))
        return super().action_confirm()
