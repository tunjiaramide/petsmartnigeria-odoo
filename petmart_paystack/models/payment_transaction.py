import re

from odoo import _, api, models
from odoo.exceptions import ValidationError
from odoo.tools import urls

from odoo.addons.payment import utils as payment_utils
from odoo.addons.payment.logging import get_payment_logger
from odoo.addons.petmart_paystack import const
from odoo.addons.petmart_paystack.controllers.main import PaystackController


_logger = get_payment_logger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _compute_reference(self, provider_code, prefix=None, separator='-', **kwargs):
        """Override of `payment` to satisfy Paystack requirements for references.

        - Only letters, digits, "-", "." and "=" are accepted ("INV/2026/0001" is refused).
        - References must be unique for the whole Paystack account, and the same test keys can be
          used by several databases, so the prefix is singularized with the current datetime.
        """
        if provider_code == 'paystack':
            if not prefix:
                # See payment_flutterwave: compute the prefix from the kwargs before singularizing
                # so that the reference is still named after the related document.
                prefix = self.sudo()._compute_reference_prefix(separator, **kwargs) or None
            if prefix:
                prefix = re.sub(r'[^A-Za-z0-9.=-]', '-', prefix)
            prefix = payment_utils.singularize_reference_prefix(prefix=prefix, separator=separator)
        return super()._compute_reference(
            provider_code, prefix=prefix, separator=separator, **kwargs
        )

    def _get_specific_rendering_values(self, processing_values):
        """ Override of payment to return Paystack-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'paystack':
            return res

        # Initialize the transaction and retrieve the link to the checkout page.
        return_url = urls.urljoin(self.provider_id.get_base_url(), PaystackController._return_url)
        payload = {
            'reference': self.reference,
            'email': self.partner_email,
            'amount': payment_utils.to_minor_currency_units(self.amount, self.currency_id),
            'currency': self.currency_id.name,
            'callback_url': return_url,
            'metadata': {
                # Where the "Cancel payment" link of the checkout page leads.
                'cancel_action': f'{return_url}?reference={self.reference}',
            },
        }
        channel = const.PAYMENT_METHODS_MAPPING.get(self.payment_method_code)
        if channel:
            payload['channels'] = [channel]
        try:
            checkout_data = self._send_api_request('POST', 'transaction/initialize', json=payload)
        except ValidationError as error:
            self._set_error(str(error))
            return {}

        return {
            'api_url': checkout_data['authorization_url'],
            'access_code': checkout_data['access_code'],
            'return_url': payload['metadata']['cancel_action'],
        }

    def _extract_amount_data(self, payment_data):
        """Override of `payment` to extract the amount and currency from the payment data."""
        if self.provider_code != 'paystack':
            return super()._extract_amount_data(payment_data)

        amount = payment_data.get('amount') or 0
        # When the account passes the Paystack fees on to the customer, the amount paid is higher
        # than the amount requested. Paying at least the requested amount is what matters.
        requested_amount = payment_data.get('requested_amount') or 0
        if requested_amount and amount >= requested_amount:
            amount = requested_amount
        return {
            'amount': payment_utils.to_major_currency_units(amount, self.currency_id),
            'currency_code': payment_data.get('currency'),
        }

    def _apply_updates(self, payment_data):
        """Override of `payment` to update the transaction based on the payment data."""
        if self.provider_code != 'paystack':
            return super()._apply_updates(payment_data)

        # Update the provider reference.
        if payment_data.get('id'):
            self.provider_reference = payment_data['id']

        # Update the payment method.
        payment_method_code = payment_data.get('channel') or ''
        if payment_method_code == 'card':
            card_type = (payment_data.get('authorization') or {}).get('card_type') or ''
            payment_method_code = card_type.strip().lower().split(' ')[0] or 'card'
        payment_method = self.env['payment.method']._get_from_code(
            payment_method_code, mapping=const.PAYMENT_METHODS_MAPPING
        )
        self.payment_method_id = payment_method or self.payment_method_id

        # Update the payment state.
        payment_status = (payment_data.get('status') or '').lower()
        if payment_status in const.PAYMENT_STATUS_MAPPING['pending']:
            self._set_pending()
        elif payment_status in const.PAYMENT_STATUS_MAPPING['done']:
            # A customer can leave the checkout page and still complete the payment afterwards.
            self._set_done(extra_allowed_states=('cancel',))
        elif payment_status in const.PAYMENT_STATUS_MAPPING['cancel']:
            self._set_canceled()
        elif payment_status in const.PAYMENT_STATUS_MAPPING['error']:
            self._set_error(_(
                "Your payment was not successful (%s). Please try again.",
                payment_data.get('gateway_response') or payment_status,
            ))
        else:
            _logger.warning(
                "Received data with invalid payment status (%s) for transaction %s.",
                payment_status, self.reference
            )
            self._set_error(_("Unknown payment status: %s", payment_status))
