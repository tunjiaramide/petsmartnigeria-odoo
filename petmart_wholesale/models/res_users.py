from odoo import api, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def signup(self, values, token=None):
        """Self-registered accounts start as 'pending' and need staff approval."""
        self_signup = not token
        if self_signup:
            values = dict(values, wholesale_state='pending')
        result = super().signup(values, token)
        if self_signup:
            self._notify_wholesale_application(result[0])
        return result

    @api.model
    def _notify_wholesale_application(self, login):
        user = self.sudo().search(self._get_login_domain(login), limit=1)
        if not user:
            return
        partner = user.partner_id
        for manager in self.env['res.partner']._wholesale_managers()[:3]:
            partner.sudo().activity_schedule(
                'mail.mail_activity_data_todo',
                summary=self.env._("Review wholesale application"),
                note=self.env._(
                    "%(name)s (%(company)s) registered for a wholesale account.",
                    name=partner.name, company=partner.company_name or '-'),
                user_id=manager.id,
            )
