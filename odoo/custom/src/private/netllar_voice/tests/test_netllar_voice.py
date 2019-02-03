# -*- coding: utf-8 -*-
# (c) 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.tests import common
from openerp import fields
from datetime import datetime
from dateutil.relativedelta import relativedelta


class TestNetllarVoice(common.TransactionCase):
    def setUp(self):
        super(TestNetllarVoice, self).setUp()
        self.contract_model = self.env['sale.telecommunications.contract']
        self.partner = self.env['res.partner'].create({'name': 'Test'})
        self.voice_product = self.env['product.product'].create(
            {'name': 'Voice product'})
        self.bond = self.env['sale.telecommunications.bond'].create(
            {'name': 'Test bond',
             'voice_exceeded_product_id': self.voice_product.id,
             'sms_exceeded_product_id': self.voice_product.id,
             'mms_exceeded_product_id': self.voice_product.id,
             'data_exceeded_product_id': self.voice_product.id})
        self.cli = self.env['sale.telecommunications.cli'].create(
            {'name': '0',
             'type': 'land'})
        self.product = self.env['product.product'].create(
            {'name': 'Test',
             'bond_id': self.bond.id})
        journal = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1)
        self.contract = self.contract_model.create(
            {'name': 'Test contract',
             'start_date': fields.Date.to_string(datetime.now()),
             'partner_id': self.partner.id,
             'journal_id': journal.id,
             'prolong': 'unlimited',
             'period_type': 'pre-paid',
             'contract_line': [
                 (0, 0, {'product_id': self.product.id,
                         'cli_id': self.cli.id})]})

    def _test_contract_line_rules(self):
        cl_rule_model = self.env['sale.telecommunications.contract.line.rule']
        contract_line = self.contract.contract_line[0]
        cl_rule_vals = {
            'name': 'Test rule 1',
            'start_date': '2014-04-01',
            'end_date': '2014-04-30',
            'contract_line_id': self.contract.contract_line[0].id,
        }
        cl_rule1 = cl_rule_model.create(cl_rule_vals)
        date = datetime(year=2014, month=3, day=31)
        self.assertTrue(cl_rule1.isValid(cl_rule1, contract_line, date))
        date = datetime(year=2014, month=4, day=1)
        self.assertTrue(cl_rule1.isValid(cl_rule1, contract_line, date))
        date = datetime(year=2014, month=4, day=10)
        self.assertTrue(cl_rule1.isValid(cl_rule1, contract_line, date))
        date = datetime(year=2014, month=4, day=30)
        self.assertTrue(cl_rule1.isValid(cl_rule1, contract_line, date))
        date = datetime(year=2014, month=5, day=1)
        self.assertTrue(cl_rule1.isValid(cl_rule1, contract_line, date))
        cl_rule_vals = {
            'name': 'Test rule 2',
            'end_date': '2014-04-30',
            'contract_line_id': self.contract.contract_line[0].id,
        }
        cl_rule2 = cl_rule_model.create(cl_rule_vals)
        date = datetime(year=2014, month=3, day=30)
        self.assertTrue(cl_rule2.isValid(cl_rule2, contract_line, date))
        date = datetime(year=2014, month=4, day=30)
        self.assertTrue(cl_rule2.isValid(cl_rule2, contract_line, date))
        date = datetime(year=2014, month=5, day=1)
        self.assertTrue(cl_rule2.isValid(cl_rule2, contract_line, date))
        cl_rule_vals = {
            'name': 'Test rule 2',
            'start_date': '2014-04-01',
            'contract_line_id': self.contract.contract_line[0].id,
        }
        cl_rule3 = cl_rule_model.create(cl_rule_vals)
        date = datetime(year=2014, month=3, day=30)
        self.assertTrue(cl_rule3.isValid(cl_rule3, contract_line, date))
        date = datetime(year=2014, month=4, day=30)
        self.assertTrue(cl_rule3.isValid(cl_rule3, contract_line, date))
        date = datetime(year=2014, month=5, day=1)
        self.assertTrue(cl_rule3.isValid(cl_rule3, contract_line, date))

    def test_cdr_line_invoice(self):
        """Tests that existing CDR lines are included in the invoice."""
        self.env['sale.telecommunications.cdr'].create(
            {'import_type': 'masmovil_csv',
             'date': self.contract.start_date,
             'line_ids': [(0, 0, {
                 'caller_id': self.cli.id,
                 'line_type': 'call',
                 'date': fields.Date.to_string(
                     datetime.now() - relativedelta(months=1)),
                 'dest': '123456789',
                 'length': 15})]})
        self.contract.make_invoices()
        self.assertEqual(
            len(self.contract.invoice_line.invoice_id.cdr_line), 1)
