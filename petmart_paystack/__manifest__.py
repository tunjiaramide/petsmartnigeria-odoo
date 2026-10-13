{
    'name': 'Payment Provider: Paystack',
    'summary': 'Pay by card or bank transfer through Paystack',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Payment Providers',
    'author': 'PETSMART Nigeria',
    'license': 'LGPL-3',
    'depends': ['payment'],
    'data': [
        'views/payment_paystack_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'petmart_paystack/static/src/interactions/payment_form.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    'installable': True,
    'application': False,
}
