from datetime import timedelta

from odoo import api, fields, models
from odoo.http import request

STOCK_STATUS = [('available', 'Available'), ('low', 'Low stock'), ('out', 'Out of stock')]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    petmart_brand = fields.Char(string='Brand')
    petmart_low_stock_threshold = fields.Float(
        string='Low-stock threshold', default=50.0,
        help="At or below this available quantity the website shows LOW STOCK. "
             "Customers never see the real quantity.")
    petmart_stock_status = fields.Selection(
        STOCK_STATUS, string='Website availability', compute='_compute_petmart_stock_status')
    petmart_is_new = fields.Boolean(string='New arrival', compute='_compute_petmart_flags')
    petmart_is_back_in_stock = fields.Boolean(string='Back in stock', compute='_compute_petmart_flags')
    petmart_was_out_of_stock = fields.Boolean(copy=False)
    petmart_back_in_stock_until = fields.Datetime(copy=False)

    @api.depends('is_storable', 'petmart_low_stock_threshold')
    def _compute_petmart_stock_status(self):
        for product in self:
            if not product.is_storable:
                product.petmart_stock_status = 'available'
                continue
            qty = sum(product.sudo().product_variant_ids.mapped('free_qty'))
            if qty <= 0:
                product.petmart_stock_status = 'out'
            elif qty <= product.petmart_low_stock_threshold:
                product.petmart_stock_status = 'low'
            else:
                product.petmart_stock_status = 'available'

    def _compute_petmart_flags(self):
        days = int(self.env['ir.config_parameter'].sudo().get_param('petmart.new_arrival_days', 30))
        now = fields.Datetime.now()
        limit = now - timedelta(days=days)
        for product in self:
            product.petmart_is_new = bool(product.create_date and product.create_date >= limit)
            until = product.petmart_back_in_stock_until
            product.petmart_is_back_in_stock = bool(until and until >= now)

    # ------------------------------------------------------------------
    # Prices are only for staff and approved wholesale customers
    # ------------------------------------------------------------------
    @api.model
    def _petmart_price_locked(self):
        """True on the website for a visitor who may browse but not see prices."""
        return bool(request) and request.is_frontend and not request.website._petmart_can_order()

    def _get_sales_prices(self, website):
        # shop listing
        if self._petmart_price_locked():
            return {template.id: {'price_reduce': 0.0} for template in self}
        return super()._get_sales_prices(website)

    def _get_additionnal_combination_info(self, product_or_template, quantity, uom, date, website):
        """Product page, search suggestions, wishlist and the variant RPC all read
        their price here. A locked visitor gets no amount at all, and Odoo's own
        "price hidden, cannot be ordered" switch (prevent_zero_price_sale)."""
        combination_info = super()._get_additionnal_combination_info(product_or_template, quantity, uom, date, website)
        if self._petmart_price_locked():
            for key in ('price', 'list_price', 'price_extra', 'compare_list_price', 'base_unit_price'):
                if key in combination_info:
                    combination_info[key] = 0.0
            combination_info.update({
                'has_discounted_price': False,
                'prevent_zero_price_sale': True,
                'petmart_price_locked': True,
            })
        return combination_info

    def _website_show_quick_add(self):
        if self._petmart_price_locked():
            return False
        return super()._website_show_quick_add()

    @api.model
    def _cron_petmart_back_in_stock(self):
        """Flag products that were out of stock and are available again (for 7 days)."""
        now = fields.Datetime.now()
        for product in self.search([('is_storable', '=', True)]):
            if product.petmart_stock_status == 'out':
                if not product.petmart_was_out_of_stock:
                    product.petmart_was_out_of_stock = True
            elif product.petmart_was_out_of_stock:
                product.write({
                    'petmart_was_out_of_stock': False,
                    'petmart_back_in_stock_until': now + timedelta(days=7),
                })
