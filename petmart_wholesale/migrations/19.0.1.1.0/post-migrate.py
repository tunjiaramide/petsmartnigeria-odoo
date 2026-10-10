from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """The catalogue is now open to visitors (prices stay hidden until a customer
    is approved), so the shop is no longer restricted to logged-in users."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['website'].search([('ecommerce_access', '=', 'logged_in')]).write({'ecommerce_access': 'everyone'})
