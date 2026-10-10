from odoo import models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _is_add_to_cart_allowed(self):
        # server-side block: only staff and approved customers can add to the cart
        if self.env['product.template']._petmart_price_locked():
            return False
        return super()._is_add_to_cart_allowed()

    def _to_markup_data(self, website):
        """No price in the page's structured data (read by search engines) for
        visitors who are not allowed to see prices."""
        markup_data = super()._to_markup_data(website)
        if self.env['product.template']._petmart_price_locked():
            markup_data.pop('offers', None)
        return markup_data
