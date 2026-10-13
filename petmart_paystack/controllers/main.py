import hashlib
import hmac
import pprint

from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

from odoo.addons.payment.logging import get_payment_logger


_logger = get_payment_logger(__name__)


class PaystackController(http.Controller):
    _return_url = '/payment/paystack/return'
    _webhook_url = '/payment/paystack/webhook'

    @http.route(_return_url, type='http', methods=['GET'], auth='public')
    def paystack_return_from_checkout(self, **data):
        """Process the payment after the customer comes back from the Paystack checkout page."""
        _logger.info("Handling redirection from Paystack with data:\n%s", pprint.pformat(data))
        self._verify_and_process(data)
        return request.redirect('/payment/status')

    @http.route(_webhook_url, type='http', methods=['POST'], auth='public', csrf=False)
    def paystack_webhook(self):
        """Process the payment data sent by Paystack to the webhook."""
        data = request.get_json_data()
        _logger.info("Notification received from Paystack with data:\n%s", pprint.pformat(data))

        if data.get('event') == 'charge.success':
            payment_data = data.get('data') or {}
            tx_sudo = request.env['payment.transaction'].sudo()._search_by_reference(
                'paystack', payment_data
            )
            if tx_sudo:
                signature = request.httprequest.headers.get('x-paystack-signature')
                self._verify_signature(signature, request.httprequest.get_data(), tx_sudo)
                tx_sudo._process('paystack', payment_data)
        return request.make_json_response('')

    @staticmethod
    def _verify_signature(received_signature, payload, tx_sudo):
        """Check that the notification was signed with the secret key of the provider.

        :raise Forbidden: If the signatures don't match.
        """
        if not received_signature:
            _logger.warning("Received payment data with missing signature.")
            raise Forbidden()

        secret_key = tx_sudo.provider_id.paystack_secret_key or ''
        expected_signature = hmac.new(secret_key.encode(), payload, hashlib.sha512).hexdigest()
        if not hmac.compare_digest(received_signature, expected_signature):
            _logger.warning("Received payment data with invalid signature.")
            raise Forbidden()

    @staticmethod
    def _verify_and_process(data):
        """Ask Paystack for the real status of the transaction and process it."""
        tx_sudo = request.env['payment.transaction'].sudo()._search_by_reference('paystack', data)
        if not tx_sudo:
            return

        try:
            verified_data = tx_sudo._send_api_request(
                'GET', f'transaction/verify/{tx_sudo.reference}'
            )
        except ValidationError:
            _logger.error("Unable to verify the payment data")
        else:
            tx_sudo._process('paystack', verified_data)
