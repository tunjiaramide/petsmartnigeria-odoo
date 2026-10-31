from odoo import SUPERUSER_ID, api

from odoo.addons.petmart_wholesale.hooks import _rename_delivery_method


def migrate(cr, version):
    """No delivery fees: the free delivery method is renamed so it no longer reads as free."""
    _rename_delivery_method(api.Environment(cr, SUPERUSER_ID, {}))
