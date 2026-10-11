from odoo import http
from odoo.exceptions import UserError
from odoo.fields import Domain
from odoo.http import request

from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.web.controllers.home import SIGN_UP_REQUEST_PARAMS
from odoo.addons.website_sale.controllers.cart import Cart
from odoo.addons.website_sale.controllers.main import WebsiteSale

# Extra fields collected on the wholesale registration form.
SIGN_UP_REQUEST_PARAMS.update({'company_name', 'phone', 'vat', 'street'})


def _order_redirect():
    """The catalogue is open to everyone, but the cart and checkout are only for
    staff and approved customers: visitors go to the login form, signed-in
    customers who are not approved yet go to their application status page."""
    if request.website._petmart_can_order():
        return None
    if request.env.user._is_public():
        return request.redirect('/web/login?redirect=/shop/cart')
    return request.redirect('/wholesale/pending')


class PetmartSignup(AuthSignupHome):

    def _prepare_signup_values(self, qcontext):
        values = super()._prepare_signup_values(qcontext)
        if not qcontext.get('token'):
            company_name = (qcontext.get('company_name') or '').strip()
            phone = (qcontext.get('phone') or '').strip()
            if not company_name or not phone:
                raise UserError(request.env._("Business name and phone number are required."))
            values.update({
                'company_name': company_name,
                'phone': phone,
                'vat': (qcontext.get('vat') or '').strip() or False,
                'street': (qcontext.get('street') or '').strip() or False,
            })
        return values


class PetmartShop(WebsiteSale):

    def _petmart_brands(self):
        """Brands ticked in the shop (?brand=<id>,<id>), or an empty recordset."""
        ids = [int(part) for part in str(request.params.get('brand') or '').split(',') if part.isdigit()]
        return request.env['petmart.brand'].sudo().browse(ids).exists()

    def _get_search_options(self, *args, **kwargs):
        options = super()._get_search_options(*args, **kwargs)
        options['petmart_brands'] = self._petmart_brands().ids
        return options

    def _get_shop_domain(self, *args, **kwargs):
        domain = super()._get_shop_domain(*args, **kwargs)
        brands = self._petmart_brands()
        if brands:
            domain &= Domain('petmart_brand_id', 'in', brands.ids)
        return domain

    def _shop_get_query_url_kwargs(self, *args, **kwargs):
        query = super()._shop_get_query_url_kwargs(*args, **kwargs)
        query['brand'] = ','.join(map(str, self._petmart_brands().ids)) or None
        return query

    def _get_additional_shop_values(self, values, **kwargs):
        """Brands that have products in the category / search being viewed. Each
        entry carries the ?brand= value that ticking or unticking it leads to."""
        res = super()._get_additional_shop_values(values, **kwargs)
        domain = super()._get_shop_domain(values.get('search'), values.get('category'), {})
        groups = request.env['product.template']._read_group(
            domain & Domain('petmart_brand_id', '!=', False), ['petmart_brand_id'], ['__count'])
        selected = self._petmart_brands()
        entries = []
        for brand, count in groups:
            toggled = selected - brand if brand in selected else selected + brand
            entries.append({
                'brand': brand.sudo(),
                'count': count,
                'checked': brand in selected,
                'toggle': ','.join(map(str, toggled.ids)) or 0,
            })
        entries.sort(key=lambda entry: (not entry['checked'], entry['brand'].name.lower()))
        res.update({'pm_brands_selected': selected, 'pm_brands': entries})
        return res

    def _check_cart(self, order_sudo):
        redirection = _order_redirect() or super()._check_cart(order_sudo)
        if redirection:
            return redirection
        if order_sudo and not order_sudo._petmart_min_order_ok():
            minimum = order_sudo._petmart_min_order_amount()
            order_sudo.shop_warning = request.env._(
                "Minimum order value is %(min)s. Please add more items to continue.",
                min=order_sudo.currency_id.format(minimum),
            )
            return request.redirect('/shop/cart')


class PetmartCart(Cart):

    @http.route()
    def cart(self, *args, **kwargs):
        return _order_redirect() or super().cart(*args, **kwargs)


class PetmartBrands(http.Controller):

    @http.route('/brands', type='http', auth='public', website=True, sitemap=True)
    def brands(self, **kw):
        groups = request.env['product.template']._read_group(
            Domain(request.website.sale_product_domain()) & Domain('petmart_brand_id', '!=', False),
            ['petmart_brand_id'], ['__count'])
        counts = {brand.id: count for brand, count in groups}
        letters = {}
        for brand in request.env['petmart.brand'].sudo().search([]):
            initial = brand.name[:1].upper()
            letters.setdefault(initial if initial.isalpha() else '#', []).append(brand)
        return request.render('petmart_wholesale.brands_page', {
            'brand_letters': sorted(letters.items()),
            'brand_counts': counts,
        })


class WholesaleStatus(http.Controller):

    @http.route('/wholesale/pending', type='http', auth='user', website=True, sitemap=False)
    def pending(self, **kw):
        state = request.website._petmart_wholesale_state()
        if state == 'approved':
            return request.redirect('/shop')
        return request.render('petmart_wholesale.pending_page', {'wholesale_state': state})

    @http.route('/wholesale/apply', type='http', auth='user', website=True, methods=['POST'], sitemap=False)
    def apply(self, **kw):
        partner = request.env.user.sudo().partner_id.commercial_partner_id
        if partner.wholesale_state in ('none', 'rejected'):
            partner.wholesale_state = 'pending'
            request.env['res.users']._notify_wholesale_application(request.env.user.login)
        return request.redirect('/wholesale/pending')
