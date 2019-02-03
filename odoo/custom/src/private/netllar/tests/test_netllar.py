# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests import common
from openerp import fields


# TODO: Test property fields with multi-company
class TestNetllar(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestNetllar, cls).setUpClass()
        cls.contract_obj = cls.env['sale.telecommunications.contract']
        cls.sale_journal = cls.env['account.journal'].create({
            'name': 'Sales Journal - (test contract)',
            'code': 'SALE',
            'type': 'sale',
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test',
            'customer': True,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'Product Test',
            'list_price': 100.00,
        })
        cls.contract = cls.contract_obj.create({
            'name': 'Test contract',
            'partner_id': cls.partner.id,
            'journal_id': cls.sale_journal.id,
            'start_date': '2016-01-01',
        })
        line_obj = cls.env['sale.telecommunications.contract.line']
        cls.contract_line = line_obj.create({
            'contract_id': cls.contract.id,
            'start_date': '2016-01-01',
            'product_id': cls.product.id,
            'quantity': 2.0,
            'price': 150.00,
            'discount': 20.0,
            'additional_description': 'Extra test',
        })

    def test_create_contract(self):
        contract = self.contract_obj.create({
            'name': 'Test contract 2',
            'partner_id': self.partner.id,
            'journal_id': self.sale_journal.id,
        })
        self.assertTrue(contract.start_date)
        self.assertTrue(contract.number)

    def test_write_contract(self):
        self.contract.invoicing_day = 1
        self.contract_line.last_invoice_date = '2016-01-01'
        self.contract.invoicing_day = 2
        self.assertEqual(self.contract_line.last_invoice_date, '2016-01-02')

    def test_copy(self):
        contract2 = self.contract.copy()
        self.assertEqual(contract2.name, 'Test contract*')
        self.assertEqual(contract2.state, 'empty')
        self.assertNotEqual(self.contract.number, contract2.number)
        self.assertTrue(contract2.active)
        self.assertEqual(contract2.start_date, fields.Date.today())
        self.assertTrue(contract2.contract_line)
        self.assertFalse(contract2.invoice_line)

    def test_flow(self):
        self.contract.make_invoices()
        invoice = self.contract.invoice_line.invoice_id
        self.assertTrue(invoice)
        inv_line = invoice.invoice_line_ids
        self.assertTrue(inv_line)
        self.assertEqual(inv_line.product_id, self.product)
        self.assertEqual(
            inv_line.name,
            u'Product Test\nExtra test\nPeriod: from 01/01/2016 to 01/31/2016',
        )
        self.assertEqual(inv_line.quantity, 2)
        self.assertEqual(inv_line.price_unit, 150)
        self.assertEqual(inv_line.discount, 20)
