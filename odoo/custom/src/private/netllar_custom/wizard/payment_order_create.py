# -*- coding: utf-8 -*-
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api


class PaymentOrderCreate(models.TransientModel):
    _inherit = 'payment.order.create'

    include_returned_invoices = fields.Boolean(
        string="Incluir devoluciones")
    mandate_selection = fields.Selection(
        selection=[('first', u'Sólo los del primer mandato (o únicos)'),
                   ('non_first', u'Todos menos los de primer mandato'),
                   ('all', u'Todos')], default='all',
        string=u"Selección de mandato")

    @api.multi
    def extend_payment_order_domain(self, payment_order, domain):
        super(PaymentOrderCreate, self).extend_payment_order_domain(
            payment_order, domain)
        if not self.include_returned_invoices:
            invoices = self.env['account.invoice'].search(
                [('returned_payment', '=', True), ('state', '=', 'open')])
            if invoices:
                domain += [('invoice', 'not in', tuple(invoices.ids))]
        mandate_domain = []
        if self.mandate_selection != 'all':
            if self.mandate_selection == 'first':
                sequence_type = ['first']
                mandate_domain += ['|', ('type', '=', 'oneoff')]
            else:
                sequence_type = ['recurring', 'final']
            mandate_domain += [
                '&', ('type', '=', 'recurrent'),
                ('recurrent_sequence_type', 'in', sequence_type)]
            mandates = self.env['account.banking.mandate'].search(
                mandate_domain)
            partners = mandates.mapped('partner_id')
            if self.mandate_selection == 'first':
                partners |= partners.search([('mandate_ids', '=', False)])
            domain += [('partner_id', 'in', partners.ids)]
        return True
