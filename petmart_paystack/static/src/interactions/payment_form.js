import { loadJS } from '@web/core/assets';
import { _t } from '@web/core/l10n/translation';
import { patch } from '@web/core/utils/patch';

import { PaymentForm } from '@payment/interactions/payment_form';

patch(PaymentForm.prototype, {

    /**
     * Open the Paystack checkout as an overlay on top of the page instead of leaving the website.
     *
     * If the Paystack script cannot be loaded, the customer is redirected to the Paystack checkout
     * page as usual.
     *
     * @override method from @payment/interactions/payment_form
     * @private
     * @param {string} providerCode - The code of the selected payment option's provider.
     * @param {number} paymentOptionId - The id of the selected payment option.
     * @param {string} paymentMethodCode - The code of the selected payment method, if any.
     * @param {object} processingValues - The processing values of the transaction.
     * @return {void}
     */
    async _processRedirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
        if (providerCode !== 'paystack') {
            return super._processRedirectFlow(...arguments);
        }
        const div = document.createElement('div');
        div.innerHTML = processingValues['redirect_form_html'];
        const { accessCode, returnUrl } = div.querySelector('form').dataset;
        try {
            await this.waitFor(loadJS('https://js.paystack.co/v2/inline.js'));
            const popup = new window.PaystackPop();
            popup.resumeTransaction(accessCode, {
                // The page must not stay blocked behind the overlay.
                onLoad: () => this._enableButton(),
                // The return page asks Paystack for the real status of the payment.
                onSuccess: () => {
                    this._disableButton(true);
                    window.location.assign(returnUrl);
                },
                onCancel: () => this._enableButton(),
                onError: (error) => {
                    this._displayErrorDialog(_t("Payment processing failed"), error?.message || '');
                    this._enableButton();
                },
            });
        } catch {
            return super._processRedirectFlow(...arguments);
        }
    },
});
