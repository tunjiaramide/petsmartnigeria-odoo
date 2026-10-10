from odoo import models


class Website(models.Model):
    _inherit = 'website'

    def _petmart_can_order(self):
        """Prices and ordering are for staff and approved wholesale customers.
        Everyone else (visitors, pending or rejected accounts) can browse the
        catalogue but never sees a price and cannot add to the cart."""
        user = self.env.user
        if user._is_internal():
            return True
        if user._is_public():
            return False
        return user.sudo().partner_id.commercial_partner_id.wholesale_state == 'approved'

    def _petmart_wholesale_state(self):
        """'public', 'none', 'pending', 'approved' or 'rejected' for the current visitor."""
        user = self.env.user
        if user._is_public():
            return 'public'
        if user._is_internal():
            return 'approved'
        return user.sudo().partner_id.commercial_partner_id.wholesale_state

    def _petmart_unlock_url(self):
        """Where a visitor who cannot see prices is sent: the login form, or the
        application status page when already signed in."""
        return '/web/login' if self.env.user._is_public() else '/wholesale/pending'
