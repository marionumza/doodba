# -*- coding: utf-8 -*-
# (c) 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields
from openerp.addons.decimal_precision import decimal_precision as dp


class AccountInvoiceFranchiseLine(models.Model):
    _name = "account.invoice.franchise_line"
    _rec_name = 'cdr_line_id'
    _order = 'date'

    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Invoice reference',
        required=True, ondelete="cascade")
    cdr_line_id = fields.Many2one(
        comodel_name='sale.telecommunications.cdr.line', string='CDR line',
        required=True, ondelete="restrict", index=True)
    price = fields.Float(
        string='Price', required=True,
        digits_compute=dp.get_precision('Voice price'))
    caller_id = fields.Many2one(
        related='cdr_line_id.caller_id', string='Source CLI',
        comodel_name='sale.telecommunications.cli')
    line_type = fields.Selection(
        related='cdr_line_id.line_type', string='Type')
    date = fields.Datetime(
        related='cdr_line_id.date', string='Call date', store=True, index=True)
    dest = fields.Char(
        related='cdr_line_id.dest', string='Destination number')
    length = fields.Integer(
        related='cdr_line_id.length', string='Amount')
    prefix = fields.Char(
        related='cdr_line_id.prefix', string='Prefix')
    customer_price = fields.Float(
        related='cdr_line_id.price', string='Customer price')


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    franchise_line = fields.One2many(
        comodel_name='account.invoice.franchise_line',
        inverse_name='invoice_id', string='Franchise lines', readonly=True)
