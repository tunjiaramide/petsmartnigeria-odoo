# The currencies supported by Paystack, in ISO 4217 format.
SUPPORTED_CURRENCIES = ['NGN', 'GHS', 'ZAR', 'KES', 'USD', 'XOF', 'EGP', 'RWF']

# Mapping of transaction states to Paystack transaction statuses.
PAYMENT_STATUS_MAPPING = {
    'pending': ['pending', 'ongoing', 'processing', 'queued'],
    'done': ['success'],
    'cancel': ['abandoned'],
    'error': ['failed', 'reversed'],
}

# The codes of the payment methods to activate when Paystack is activated.
DEFAULT_PAYMENT_METHOD_CODES = {
    # Primary payment methods.
    'card',
    'bank_transfer',
    # Brand payment methods.
    'visa',
    'mastercard',
}

# Payment method code -> Paystack checkout channel.
PAYMENT_METHODS_MAPPING = {
    'card': 'card',
    'bank_transfer': 'bank_transfer',
    'ussd': 'ussd',
    'mobile_money': 'mobile_money',
}
