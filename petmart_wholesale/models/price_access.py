from odoo import api, models
from odoo.http import request

# Customer accounts can read products, price lists and wishlists through Odoo's data
# interface (/web/dataset/call_kw, /json/2), not only through the website pages. The website
# hides prices by its own rules (see product_template.py); these fields close the back door.

# hidden from customers who may not see prices (pending, rejected, suspended accounts)
LOCKED_PRICE_FIELDS = {
    'product.template': {'list_price', 'compare_list_price', 'base_unit_price'},
    'product.product': {'list_price', 'lst_price', 'price_extra', 'compare_list_price', 'base_unit_price'},
    'product.template.attribute.value': {'price_extra'},
    'product.attribute.value': {'default_extra_price'},
    'product.wishlist': {'price'},
}

# hidden from every customer, approved or not: what PETSMART pays for stock, and the price
# list rules (an approved Retailer must not read the Wholesale or Distributor prices)
STAFF_ONLY_FIELDS = {
    'product.product': {'avg_cost', 'total_value'},
    'product.pricelist.item': {
        'fixed_price', 'percent_price', 'price_discount', 'price_round', 'price_surcharge',
        'price_markup', 'price_min_margin', 'price_max_margin', 'price',
    },
}


def _petmart_field_hidden(model, field):
    """True when a customer reads one of the fields above outside the website pages."""
    staff_only = field.name in STAFF_ONLY_FIELDS.get(model._name, ())
    if not staff_only and field.name not in LOCKED_PRICE_FIELDS.get(model._name, ()):
        return False
    if model.env.su or not request or getattr(request, 'is_frontend', False):
        return False
    if model.env.user._is_internal():
        return False
    return staff_only or not model.env['website']._petmart_can_order()


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def _has_field_access(self, field, operation):
        return not _petmart_field_hidden(self, field) and super()._has_field_access(field, operation)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def _has_field_access(self, field, operation):
        return not _petmart_field_hidden(self, field) and super()._has_field_access(field, operation)


class ProductTemplateAttributeValue(models.Model):
    _inherit = 'product.template.attribute.value'

    @api.model
    def _has_field_access(self, field, operation):
        return not _petmart_field_hidden(self, field) and super()._has_field_access(field, operation)

    def _get_extra_price(self, combination_info):
        # product page size options: no "+ ₦20,000" badge when the price is locked
        if combination_info.get('petmart_price_locked'):
            return 0.0
        return super()._get_extra_price(combination_info)


class ProductAttributeValue(models.Model):
    _inherit = 'product.attribute.value'

    @api.model
    def _has_field_access(self, field, operation):
        return not _petmart_field_hidden(self, field) and super()._has_field_access(field, operation)


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    @api.model
    def _has_field_access(self, field, operation):
        return not _petmart_field_hidden(self, field) and super()._has_field_access(field, operation)


class ProductWishlist(models.Model):
    _inherit = 'product.wishlist'

    @api.model
    def _has_field_access(self, field, operation):
        return not _petmart_field_hidden(self, field) and super()._has_field_access(field, operation)
