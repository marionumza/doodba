# -*- coding: utf-8 -*-
from openerp import models, fields, api


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"
    _order = 'state,default_bank desc,acc_number'

    default_bank = fields.Boolean('Default bank', default=True)

    @api.model
    def create(self, vals):
        if all(x in vals for x in ['default_bank', 'partner_id', 'state']):
            banks = self.env['res.partner.bank'].search(
                [('partner_id', '=', vals['partner_id']),
                 ('state', '=', vals['state']),
                 ('default_bank', '=', True)])
            banks.write({'default_bank': False})
        return super(ResPartnerBank, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('default_bank'):
            for record in self:
                partner_id = vals.get('partner_id') or record.partner_id.id
                state = vals.get('state') or record.state
                banks = self.env['res.partner.bank'].search(
                    [('partner_id', '=', partner_id),
                     ('id', '!=', record.id),
                     ('state', '=', state),
                     ('default_bank', '=', True)])
                banks.write({'default_bank': False})
        return super(ResPartnerBank, self).write(vals)
