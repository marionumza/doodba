# -*- coding: utf-8 -*-
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.tests.common import TransactionCase


class TestPaymentReturn(TransactionCase):

    def setUp(self):
        super(TestPaymentReturn, self).setUp()
        self.invoice_model = self.env['account.invoice'].with_context(
            force_company=self.env.user.company_id.id)
        self.payment_return_model = self.env['payment.return']
        self.partner = self.env['res.partner'].create({'name': 'Test'})
        # Prepare invoice and pay it for making the return
        invoice_vals = {
            'journal_id': self.env['account.journal'].search(
                [('type', '=', 'sale')], limit=1).id,
            'type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line': [
                (0, 0, {'name': 'Test',
                        'price_unit': 20.0,
                        'quantity': 1.0,
                        'account_id': self.env['ir.property'].get(
                            'property_account_income_categ',
                            'product.category').id})]
        }
        invoice_vals.update(self.invoice_model.onchange_partner_id(
            invoice_vals['type'], invoice_vals['partner_id'])['value'])
        invoice_vals['payment_term'] = False
        self.invoice = self.invoice_model.create(invoice_vals)
        self.invoice.signal_workflow('invoice_open')
        self.receivable_line = self.invoice.move_id.line_id.filtered(
            lambda x: x.account_id.type == 'receivable')
        # Invert the move to simulate the payment
        self.payment_move = self.invoice.move_id.copy()
        for move_line in self.payment_move.line_id:
            debit = move_line.debit
            move_line.write({'debit': move_line.credit,
                             'credit': debit})
        self.payment_line = self.payment_move.line_id.filtered(
            lambda x: x.account_id.type == 'receivable')
        # Reconcile both
        self.reconcile = self.env['account.move.reconcile'].create(
            {'type': 'manual',
             'line_id': [(4, self.payment_line.id),
                         (4, self.receivable_line.id)]})
        # Create payment return
        bank_journal = self.env['account.journal'].search(
            [('type', '=', 'bank'),
             ('company_id', '=', self.env.user.company_id.id)], limit=1)
        self.payment_return = self.payment_return_model.create(
            {'journal_id': bank_journal.id,
             'line_ids': [
                 (0, 0, {'partner_id': self.partner.id,
                         'move_line_id': self.receivable_line.id,
                         'amount': self.receivable_line.debit})]})

    def test_include_return_payment_order(self):
        self.payment_return.action_confirm()
        wizard = self.env['payment.order.create'].create(
            {'include_returned_invoices': True,
             'duedate': self.invoice.date_invoice})
        payment_order = self.env['payment.order'].create(
            {'mode': self.env['payment.mode'].search(
                [('company_id', '=', self.env.user.company_id.id)],
                limit=1).id})
        action = wizard.with_context(
            active_id=payment_order.id).search_entries()
        move = self.env['account.move.line'].search(
            [('partner_id', '=', self.partner.id),
             ('id', 'in', action['context']['line_ids'])])
        self.assertEqual(len(move), 1)
        self.assertEqual(move.debit, 20.0)
