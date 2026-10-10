from odoo import http
from odoo.exceptions import UserError
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
