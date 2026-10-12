from odoo import fields, http
from odoo.exceptions import UserError
from odoo.fields import Domain
from odoo.http import request

from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.website_sale.controllers.cart import Cart
from odoo.addons.website_sale.controllers.main import WebsiteSale

# Registration form (/web/signup): what the customer fills in. Names are res.partner fields
# unless handled separately in _prepare_signup_values.
SIGNUP_REQUIRED = [
    ('company_name', "Registered business name"),
    ('wholesale_business_type', "Business type"),
    ('building', "Shop / suite / building number"),
    ('street', "Street address"),
    ('street2', "Area / neighbourhood"),
    ('city', "City / town"),
    ('state_id', "State"),
    ('country_id', "Country"),
    ('wholesale_contact_role', "Position / role"),
    ('phone', "Mobile phone number"),
    ('wholesale_whatsapp', "WhatsApp number"),
    ('wholesale_monthly_purchase', "Estimated monthly purchase value"),
    ('wholesale_territory_state_id', "Primary sales territory"),
    ('wholesale_customer_type', "Customer type"),
    ('wholesale_heard_from', "How did you hear about Pets-Mart"),
]
SIGNUP_TEXT = [
    'company_name', 'street2', 'city', 'phone', 'vat',
    'wholesale_trading_name', 'wholesale_business_type_other', 'wholesale_cac_number',
    'wholesale_year_established', 'wholesale_branch_count', 'wholesale_landmark', 'wholesale_maps_link',
    'wholesale_delivery_address', 'wholesale_contact_role_other', 'wholesale_whatsapp', 'wholesale_alt_contact',
    'wholesale_brands_stocked', 'wholesale_initial_order_value', 'wholesale_major_suppliers',
    'wholesale_areas_served', 'wholesale_retail_customers', 'wholesale_logistics',
    'wholesale_trade_references', 'wholesale_referral_name', 'wholesale_brands_wanted', 'wholesale_comments',
]
SIGNUP_SELECTION = [
    'wholesale_business_type', 'wholesale_contact_role', 'wholesale_monthly_purchase',
    'wholesale_order_frequency', 'wholesale_customer_type', 'wholesale_has_storage', 'wholesale_heard_from',
]
# Optional verification documents, saved as attachments on the contact.
SIGNUP_DOCUMENTS = [
    ('doc_cac', "CAC certificate"),
    ('doc_premises', "Business premises photograph"),
    ('doc_licence', "Veterinary practice licence"),
]
DOCUMENT_TYPES = ('.pdf', '.jpg', '.jpeg', '.png')
DOCUMENT_MAX_SIZE = 5 * 1024 * 1024


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

    def get_auth_signup_qcontext(self):
        """Lists for the registration form, and what was typed so far (so a
        rejected submission does not have to be filled in again)."""
        qcontext = super().get_auth_signup_qcontext()
        if qcontext.get('token'):
            return qcontext
        env = request.env
        form = request.httprequest.form
        nigeria = env.ref('base.ng')
        qcontext.update({
            'pm_form': {key: value for key, value in form.items() if 'password' not in key},
            'pm_form_categories': form.getlist('wholesale_category_ids'),
            'pm_selections': {
                name: env['res.partner']._fields[name]._description_selection(env) for name in SIGNUP_SELECTION},
            'pm_states': env['res.country.state'].sudo().search([('country_id', '=', nigeria.id)]),
            'pm_countries': env['res.country'].sudo().search([]),
            'pm_nigeria': nigeria,
            'pm_categories': env['website']._petmart_nav_categories(),
        })
        return qcontext

    def _petmart_signup_documents(self):
        """Uploaded verification documents as (label, filename, content)."""
        documents = []
        for key, label in SIGNUP_DOCUMENTS:
            upload = request.httprequest.files.get(key)
            if not upload or not upload.filename:
                continue
            if not upload.filename.lower().endswith(DOCUMENT_TYPES):
                raise UserError(request.env._("%(document)s: please upload a PDF, JPG or PNG file.", document=label))
            content = upload.read(DOCUMENT_MAX_SIZE + 1)
            upload.seek(0)
            if len(content) > DOCUMENT_MAX_SIZE:
                raise UserError(request.env._("%(document)s: the file is larger than 5 MB.", document=label))
            documents.append((label, upload.filename, content))
        return documents

    def _prepare_signup_values(self, qcontext):
        values = super()._prepare_signup_values(qcontext)
        if qcontext.get('token'):
            return values
        env = request.env
        form = request.httprequest.form
        text = lambda key: (form.get(key) or '').strip()

        missing = [label for key, label in SIGNUP_REQUIRED if not text(key)]
        categories = env['product.public.category'].sudo().browse(
            [int(value) for value in form.getlist('wholesale_category_ids') if value.isdigit()]).exists()
        if not categories:
            missing.append(env._("Product categories of interest"))
        if not form.get('accept_terms'):
            missing.append(env._("Acceptance of the B2B terms and conditions"))
        if not form.get('accept_privacy'):
            missing.append(env._("Acknowledgement of the privacy notice"))
        if missing:
            raise UserError(env._("Please complete: %(fields)s.", fields=', '.join(missing)))

        Partner = env['res.partner']
        for name in SIGNUP_SELECTION:
            if text(name) and text(name) not in dict(Partner._fields[name].selection):
                raise UserError(env._("The form was not properly filled in."))
        records = {}
        for name, model in (('state_id', 'res.country.state'), ('country_id', 'res.country'),
                            ('wholesale_territory_state_id', 'res.country.state')):
            record = env[model].sudo().browse(int(text(name)) if text(name).isdigit() else 0).exists()
            if not record:
                raise UserError(env._("The form was not properly filled in."))
            records[name] = record.id
        self._petmart_signup_documents()  # refuse wrong or oversized files before the account exists

        values.update({name: text(name) or False for name in SIGNUP_TEXT})
        values.update({name: text(name) or False for name in SIGNUP_SELECTION})
        values.update(records)
        values.update({
            'street': ', '.join(part for part in (text('building'), text('street')) if part),
            'website': text('business_website') or False,
            'wholesale_category_ids': [fields.Command.set(categories.ids)],
            'wholesale_terms_accepted_on': fields.Datetime.now(),
            'wholesale_marketing_consent': bool(form.get('wholesale_marketing_consent')),
        })
        return values

    def do_signup(self, qcontext, *args, **kwargs):
        res = super().do_signup(qcontext, *args, **kwargs)
        if qcontext.get('token'):
            return res
        Users = request.env['res.users'].sudo()
        user = Users.search(Users._get_login_domain(qcontext.get('login')), limit=1)
        for label, filename, content in self._petmart_signup_documents() if user else []:
            request.env['ir.attachment'].sudo().create({
                'name': '%s - %s' % (label, filename),
                'raw': content,
                'res_model': 'res.partner',
                'res_id': user.partner_id.id,
            })
        return res


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

    @http.route('/wholesale/terms', type='http', auth='public', website=True, sitemap=True)
    def terms(self, **kw):
        return request.render('petmart_wholesale.terms_page')

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
