{
    'name': 'PETSMART Nigeria Theme',
    'summary': 'Homepage, header, footer and shop styling for the PETSMART wholesale site',
    'version': '19.0.1.2.0',
    'category': 'Website/Theme',
    'author': 'PETSMART Nigeria',
    'license': 'LGPL-3',
    'depends': ['website', 'website_sale', 'petmart_wholesale'],
    'data': [
        'data/categories.xml',
        'data/shop_rules.xml',
        'views/layout.xml',
        'views/homepage.xml',
        'views/shop.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'petmart_theme/static/src/scss/petmart.scss',
            'petmart_theme/static/src/js/petmart.js',
        ],
    },
    'installable': True,
    'application': False,
}
