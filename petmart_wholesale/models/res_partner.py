from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

# Pricing tier -> pricelist given to the customer on approval.
TIER_PRICELISTS = {
    'retailer': 'petmart_wholesale.pricelist_retailer',
    'wholesale': 'petmart_wholesale.pricelist_wholesale',
    'distributor': 'petmart_wholesale.pricelist_distributor',
}


class ResPartner(models.Model):
    _inherit = 'res.partner'

    wholesale_state = fields.Selection(
        [
            ('none', 'Not applied'),
            ('pending', 'Pending approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('suspended', 'Suspended'),
        ],
        string='Wholesale status',
        default='none',
        copy=False,
        tracking=True,
    )
    wholesale_approved_by = fields.Many2one('res.users', string='Approval officer', copy=False, readonly=True)
    wholesale_approved_on = fields.Datetime(string='Approved on', copy=False, readonly=True)

    # ------------------------------------------------------------------
    # Registration form (filled in by the customer on /web/signup)
    # ------------------------------------------------------------------
    # 1. Business information ("Registered business name" is company_name, the website is `website`)
    wholesale_trading_name = fields.Char(string='Trading name')
    wholesale_business_type = fields.Selection(
        [
            ('distributor', 'Distributor'),
            ('wholesaler', 'Wholesaler'),
            ('pet_shop', 'Pet Shop'),
            ('vet_clinic', 'Veterinary Clinic'),
            ('breeder', 'Breeder'),
            ('grooming', 'Grooming Salon'),
            ('online_store', 'Online Pet Store'),
            ('other', 'Other'),
        ], string='Business type')
    wholesale_business_type_other = fields.Char(string='Other business type')
    wholesale_cac_number = fields.Char(string='CAC registration number')
    wholesale_year_established = fields.Char(string='Year established')
    wholesale_branch_count = fields.Char(string='Branches / outlets')
    # 2. Business address (street, street2 = area, city, state_id, country_id are the standard fields)
    wholesale_landmark = fields.Char(string='Nearest landmark')
    wholesale_maps_link = fields.Char(string='Google Maps link')
    wholesale_delivery_address = fields.Text(string='Additional delivery address')
    # 3. Contact person (name, email and phone are the standard fields)
    wholesale_contact_role = fields.Selection(
        [
            ('owner', 'Owner'),
            ('md', 'Managing Director'),
            ('purchasing', 'Purchasing Manager'),
            ('vet', 'Veterinarian'),
            ('store_manager', 'Store Manager'),
            ('other', 'Other'),
        ], string='Position / role')
    wholesale_contact_role_other = fields.Char(string='Other role')
    wholesale_whatsapp = fields.Char(string='WhatsApp number')
    wholesale_alt_contact = fields.Char(string='Alternative contact')
    # 4. Purchasing profile
    wholesale_monthly_purchase = fields.Selection(
        [
            ('lt_250k', 'Below ₦250,000'),
            ('250k_1m', '₦250,000 – ₦1 million'),
            ('1m_5m', '₦1 million – ₦5 million'),
            ('5m_10m', '₦5 million – ₦10 million'),
            ('gt_10m', 'Above ₦10 million'),
        ], string='Estimated monthly purchase')
    wholesale_category_ids = fields.Many2many(
        'product.public.category', 'petmart_partner_category_interest_rel', 'partner_id', 'category_id',
        string='Product categories of interest')
    wholesale_brands_stocked = fields.Char(string='Brands currently stocked')
    wholesale_order_frequency = fields.Selection(
        [
            ('weekly', 'Weekly'),
            ('fortnightly', 'Every two weeks'),
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('as_needed', 'As needed'),
        ], string='Preferred order frequency')
    wholesale_initial_order_value = fields.Char(string='Initial estimated order value')
    wholesale_major_suppliers = fields.Char(string='Current major suppliers')
    # 5. Distribution and market coverage
    wholesale_territory_state_id = fields.Many2one('res.country.state', string='Primary sales territory')
    wholesale_areas_served = fields.Char(string='Areas / states served')
    wholesale_customer_type = fields.Selection(
        [('retail', 'Retail'), ('wholesale', 'Wholesale'), ('both', 'Both')], string='Sells to')
    wholesale_retail_customers = fields.Char(string='Retail customers supplied')
    wholesale_has_storage = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Warehouse / storage facility')
    wholesale_logistics = fields.Char(string='Delivery / logistics capability')
    # 6. Business verification (TIN is `vat`; uploaded documents are attachments on the contact)
    wholesale_trade_references = fields.Text(string='Trade references')
    # 7. Marketing and referral
    wholesale_heard_from = fields.Selection(
        [
            ('sales_rep', 'Pets-Mart sales representative'),
            ('referral', 'Referred by another business'),
            ('petshop_plus', 'PetShop Plus store'),
            ('social', 'Social media'),
            ('search', 'Online search'),
            ('event', 'Trade event / exhibition'),
            ('other', 'Other'),
        ], string='How they heard about us')
    wholesale_referral_name = fields.Char(string='Sales rep / referral name')
    wholesale_brands_wanted = fields.Char(string='Brands / products requested')
    wholesale_comments = fields.Text(string='Additional comments')
    # 8. Agreement
    wholesale_terms_accepted_on = fields.Datetime(string='Terms and privacy notice accepted on', readonly=True, copy=False)
    wholesale_marketing_consent = fields.Boolean(string='Agreed to promotional WhatsApp / email')

    # ------------------------------------------------------------------
    # Staff-controlled fields (never shown to the customer)
    # ------------------------------------------------------------------
    wholesale_customer_category = fields.Selection(
        [('retailer', 'Retailer'), ('distributor', 'Distributor'), ('key_account', 'Key Account')],
        string='Customer category', tracking=True)
    wholesale_pricing_tier = fields.Selection(
        [('retailer', 'Retailer'), ('wholesale', 'Wholesale'), ('distributor', 'Distributor')],
        string='Pricing tier', tracking=True,
        help="Decides which price list the customer buys from once approved.")
    wholesale_credit_terms = fields.Selection(
        [('prepaid', 'Prepaid'), ('credit', 'Credit')], string='Credit terms', default='prepaid', tracking=True)
    wholesale_credit_limit = fields.Float(string='Credit limit', tracking=True)

    def _check_wholesale_manager(self):
        if not self.env.user.has_group('petmart_wholesale.group_petmart_editor'):
            raise AccessError(_("Only PETSMART Editors and administrators can approve or reject wholesale accounts."))

    def _wholesale_apply_pricelist(self):
        """Give approved customers the price list of their pricing tier."""
        companies = self.env['res.company'].sudo().search([])
        for partner in self.filtered(lambda p: p.wholesale_state == 'approved' and p.wholesale_pricing_tier):
            pricelist = self.env.ref(TIER_PRICELISTS[partner.wholesale_pricing_tier])
            # company-dependent property: set it for every company
            for company in companies:
                partner.with_company(company).sudo().property_product_pricelist = pricelist

    def write(self, vals):
        res = super().write(vals)
        if 'wholesale_pricing_tier' in vals:
            self._wholesale_apply_pricelist()
        return res

    def action_wholesale_approve(self):
        self._check_wholesale_manager()
        missing = self.filtered(lambda p: not p.wholesale_pricing_tier)
        if missing:
            raise UserError(_(
                "Choose a pricing tier (Wholesale application tab) before approving: %(names)s",
                names=', '.join(missing.mapped('display_name'))))
        for partner in self:
            partner.write({
                'wholesale_state': 'approved',
                'wholesale_approved_by': self.env.user.id,
                'wholesale_approved_on': fields.Datetime.now(),
            })
            partner._wholesale_apply_pricelist()
            partner.message_post(
                body=_("Your wholesale account is approved. Wholesale pricing is now enabled."),
                subject=_("Your PETSMART wholesale account is approved"),
                partner_ids=partner.ids,
                subtype_xmlid='mail.mt_comment',
            )
        return True

    def action_wholesale_reject(self):
        self._check_wholesale_manager()
        self.write({'wholesale_state': 'rejected'})
        return True

    def action_wholesale_suspend(self):
        self._check_wholesale_manager()
        self.write({'wholesale_state': 'suspended'})
        return True

    def action_wholesale_reset(self):
        self._check_wholesale_manager()
        self.write({'wholesale_state': 'pending'})
        return True

    @api.model
    def _wholesale_managers(self):
        users = self.env['res.users'].sudo().search([('share', '=', False)])
        return users.filtered(lambda u: u.has_group('petmart_wholesale.group_petmart_editor'))
