from odoo import SUPERUSER_ID, api


def post_init_hook(env):
    """One-time shop configuration for a wholesale (B2B) site."""
    # Shop is only for logged-in, approved customers; new accounts need approval.
    env['website'].search([]).write({'ecommerce_access': 'logged_in', 'auth_signup_uninvited': 'b2c'})

    # Lots / expiration dates and lot numbers on delivery slips (stock + product_expiry).
    settings = env['res.config.settings'].create({
        'group_stock_production_lot': True,
        'group_lot_on_delivery_slip': True,
    })
    settings.execute()
