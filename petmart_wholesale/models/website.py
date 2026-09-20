from odoo import models


class Website(models.Model):
    _inherit = 'website'

    def has_ecommerce_access(self):
        """Wholesale shop: only approved customers (or staff) get in when the
        shop is set to 'logged in users only'."""
        allowed = super().has_ecommerce_access()
        if not allowed or self.ecommerce_access != 'logged_in':
            return allowed
        user = self.env.user
        if user._is_internal():
            return True
        return user.sudo().partner_id.commercial_partner_id.wholesale_state == 'approved'

    def _petmart_wholesale_state(self):
        """'public', 'none', 'pending', 'approved' or 'rejected' for the current visitor."""
        user = self.env.user
        if user._is_public():
            return 'public'
        if user._is_internal():
            return 'approved'
        return user.sudo().partner_id.commercial_partner_id.wholesale_state
