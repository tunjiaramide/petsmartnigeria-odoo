from odoo import _, api, fields, models
from odoo.exceptions import AccessError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    wholesale_state = fields.Selection(
        [
            ('none', 'Not applied'),
            ('pending', 'Pending approval'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        string='Wholesale status',
        default='none',
        copy=False,
        tracking=True,
    )
    wholesale_approved_by = fields.Many2one('res.users', copy=False, readonly=True)
    wholesale_approved_on = fields.Datetime(copy=False, readonly=True)

    def _check_wholesale_manager(self):
        if not self.env.user.has_group('petmart_wholesale.group_petmart_editor'):
            raise AccessError(_("Only PETSMART Editors and administrators can approve or reject wholesale accounts."))

    def action_wholesale_approve(self):
        self._check_wholesale_manager()
        pricelist = self.env.ref('petmart_wholesale.pricelist_wholesale')
        companies = self.env['res.company'].sudo().search([])
        for partner in self:
            partner.write({
                'wholesale_state': 'approved',
                'wholesale_approved_by': self.env.user.id,
                'wholesale_approved_on': fields.Datetime.now(),
            })
            # company-dependent property: set it for every company
            for company in companies:
                partner.with_company(company).sudo().property_product_pricelist = pricelist
            partner.message_post(
                body=_("Your wholesale account is approved. Wholesale pricing is now enabled."),
                subject=_("Your PETSMART wholesale account is approved"),
                partner_ids=partner.ids,
                subtype_xmlid='mail.mt_comment',
            )
        return True

    def action_wholesale_reject(self):
        self._check_wholesale_manager()
        self.write({'wholesale_state': 'rejected'})
        return True

    def action_wholesale_reset(self):
        self._check_wholesale_manager()
        self.write({'wholesale_state': 'pending'})
        return True

    @api.model
    def _wholesale_managers(self):
        users = self.env['res.users'].sudo().search([('share', '=', False)])
        return users.filtered(lambda u: u.has_group('petmart_wholesale.group_petmart_editor'))
