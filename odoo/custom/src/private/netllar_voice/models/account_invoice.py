# -*- coding: utf-8 -*-
# (c) 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    cdr_line = fields.One2many(
        comodel_name='sale.telecommunications.cdr.line',
        inverse_name='invoice_id', string='CDR Lines', readonly=True)
