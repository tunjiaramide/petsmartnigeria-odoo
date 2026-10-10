from odoo import SUPERUSER_ID, api


def post_init_hook(env):
    """One-time shop configuration for a wholesale (B2B) site."""
    # Anyone can browse the catalogue; prices and ordering are unlocked per customer on approval
    # (see website._petmart_can_order). Visitors can register themselves.
    env['website'].search([]).write({'ecommerce_access': 'everyone', 'auth_signup_uninvited': 'b2c'})

    # Lots / expiration dates and lot numbers on delivery slips (stock + product_expiry).
    settings = env['res.config.settings'].create({
        'group_stock_production_lot': True,
        'group_lot_on_delivery_slip': True,
    })
    settings.execute()
