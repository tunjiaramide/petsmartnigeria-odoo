from odoo import fields, models
from odoo.tools.urls import urljoin as url_join

from odoo.addons.petmart_paystack import const


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('paystack', "Paystack")], ondelete={'paystack': 'set default'}
    )
    paystack_public_key = fields.Char(
        string="Paystack Public Key",
        help="The key solely used to identify the account with Paystack.",
        required_if_provider='paystack',
        copy=False,
    )
    paystack_secret_key = fields.Char(
        string="Paystack Secret Key",
        required_if_provider='paystack',
        copy=False,
        groups='base.group_system',
    )

    def _get_supported_currencies(self):
        """ Override of `payment` to return the supported currencies. """
        supported_currencies = super()._get_supported_currencies()
        if self.code == 'paystack':
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies

    def _get_default_payment_method_codes(self):
        """ Override of `payment` to return the default payment method codes. """
        self.ensure_one()
        if self.code != 'paystack':
            return super()._get_default_payment_method_codes()
        return const.DEFAULT_PAYMENT_METHOD_CODES

    # === REQUEST HELPERS === #

    def _build_request_url(self, endpoint, **kwargs):
        """Override of `payment` to build the request URL."""
        if self.code != 'paystack':
            return super()._build_request_url(endpoint, **kwargs)
        return url_join('https://api.paystack.co/', endpoint)

    def _build_request_headers(self, *args, **kwargs):
        """Override of `payment` to build the request headers."""
        if self.code != 'paystack':
            return super()._build_request_headers(*args, **kwargs)
        return {'Authorization': f'Bearer {self.paystack_secret_key}'}

    def _parse_response_error(self, response):
        """Override of `payment` to parse the error message."""
        if self.code != 'paystack':
            return super()._parse_response_error(response)
        return response.json().get('message', '')

    def _parse_response_content(self, response, **kwargs):
        """Override of `payment` to parse the response content."""
        if self.code != 'paystack':
            return super()._parse_response_content(response, **kwargs)
        return response.json()['data']
