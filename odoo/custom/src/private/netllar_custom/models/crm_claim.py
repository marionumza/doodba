# -*- coding: utf-8 -*-
# (c) 2015 Serv. Tecnol. Avanzados - Oihane Crucelaegui
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models


class CrmClaim(models.Model):
    _inherit = 'crm.claim'

    partner_contact_address = fields.Char(compute='_compute_claim_address',
                                          string='Complete Address')
    days_open = fields.Integer(compute='_compute_days_open')

    @api.multi
    def _compute_days_open(self):
        for claim in self:
            claim.days_open = (
                fields.Datetime.from_string(
                    fields.Date.context_today(self)).date() -
                fields.Datetime.from_string(claim.date).date()).days

    @api.one
    def _compute_claim_address(self):
        address = [self.partner_id.street or '', self.partner_id.city or '',
                   self.partner_id.state_id.display_name or '']
        self.partner_contact_address = ' '.join(address)


class CrmClaimData(models.Model):
    _inherit = 'crm.claim.stage'

    close = fields.Boolean(
        string='Close Claim',
        help='If claim is in this stage it will be considered as closed')
