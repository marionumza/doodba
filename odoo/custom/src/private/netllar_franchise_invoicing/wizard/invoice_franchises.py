# -*- coding: utf-8 -*-
# (c) 2014-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api, _


class InvoiceFranchises(models.TransientModel):
    _name = "account.telecommunications.invoice_franchises"
    _description = "CDR lines invoiced to franchise"

    journal_id = fields.Many2one(
        comodel_name='account.journal', string='Journal', required=True,
        help="Journal where invoices are going to be created",
        domain=[('type', '=', 'sale')])
    company_ids = fields.Many2many(
        'res.company', 'franchise_company_rel', 'inv_franchise_id',
        'company_id', string='Companies', required=True)
    date_from = fields.Date(string='Date from', required=True)
    date_to = fields.Date(string='Date to', required=True)

    def _groupRecords(self, records, field):
        groups = {}
        for record in records:
            if record[field] in groups:
                groups[record[field]].append(record)
            else:
                groups[record[field]] = [record]
        return groups

    @api.model
    def _prepare_franchise_invoice_header(self, company_id, company,
                                          journal_id):
        invoice_obj = self.env['account.invoice']
        # Prepare record
        invoice = {
            'partner_id': company.partner_id.id,
            'journal_id': journal_id,
            'type': 'out_invoice',
            'state': 'draft',
            'currency_id': company.currency_id.id,
            'company_id': company_id,
            'date_invoice': fields.Date.today(),
        }
        # Get other invoice values from partner
        invoice.update(invoice_obj.onchange_partner_id(
            type=invoice['type'], company_id=company_id,
            partner_id=company.partner_id.id,)['value'])
        return invoice

    @api.multi
    def action_invoice(self):
        data = self[:1]
        from_date = fields.Date.from_string(data.date_from)
        to_date = fields.Date.from_string(data.date_to)
        company_id = 1  # Force first company
        lang_obj = self.env['res.lang']
        contract_obj = self.env['sale.telecommunications.contract'].sudo()
        invoice_obj = self.env['account.invoice']
        invoice_line_obj = self.env['account.invoice.line']
        franch_line_obj = self.env['account.invoice.franchise_line']
        for company in data.company_ids:
            # Get lang record for format purposes
            if company.partner_id.lang:
                lang_code = company.partner_id.lang
            elif self.env.context.get('lang'):
                lang_code = self.evn.context['lang']
            else:
                lang_code = self.env.user.context_lang
            lang = lang_obj.search([('code', '=', lang_code)])
            # Get contracts for that company
            contracts = contract_obj.search([('company_id', '=', company.id)])
            # Prepare invoice header
            ctx = self.env.context.copy()
            ctx['company_id'] = company_id
            ctx['force_company'] = company_id
            ctx['type'] = 'out_invoice'
            invoice_vals = \
                self.with_context(ctx)._prepare_franchise_invoice_header(
                    company_id, company, data.journal_id.id)
            # LINES FOR FIXED FEE
            product_lines = {}
            consume_lines = {}
            price_lines = {}
            for contract in contracts:
                if (contract.start_date > data.date_to or
                        (contract.end_date and
                         contract.end_date < data.date_from)):
                    continue
                for contract_line in contract.contract_line:
                    if (not contract_line.product_id.bond_id or
                            (contract_line.start_date and
                             contract_line.start_date > data.date_to) or
                            (contract_line.end_date and
                             contract_line.end_date < data.date_from)):
                        continue
                    # Hack the method to force the quota calculation as
                    # a pre-paid contract
                    quota_dict = contract_line._get_quota(
                        from_date, period_type='pre-paid')
                    product_lines[contract_line.product_id.id] = (
                        product_lines.get(contract_line.product_id.id, 0) +
                        quota_dict['quota'])
                    price_lines_temp, invoice_lines = \
                        contract_obj._add_invoice_lines_postpaid(
                            contract_line, from_date, to_date,
                            quota_dict['quota'], invoice_vals,
                            is_franchise=True)
                    price_lines.update(price_lines_temp)
                    # Write consume lines
                    for invoice_line_vals in invoice_lines:
                        if consume_lines.get(invoice_line_vals['name']):
                            consume_line = consume_lines[
                                invoice_line_vals['name']]
                            consume_line['price_unit'] += (
                                invoice_line_vals['price_unit'])
                        else:
                            consume_lines[invoice_line_vals['name']] = (
                                invoice_line_vals)
            if product_lines or consume_lines:
                invoice = invoice_obj.with_context(ctx).create(invoice_vals)
            # Write franchise lines
            for cdr_line, price in price_lines.iteritems():
                franch_line_obj.create(
                    {'invoice_id': invoice.id,
                     'cdr_line_id': cdr_line.id,
                     'price': price})
            # Write fixed fee invoice line
            for product_id, quantity in product_lines.iteritems():
                invoice_line_vals = {
                    'product_id': product_id,
                    'quantity': quantity,
                    'invoice_id': invoice.id,
                }
                contract_obj._get_extra_values_invoice_line(
                    invoice_vals, invoice_line_vals)
                invoice_line_vals['name'] += (
                    '\n' + _('Period: from %s to %s') %
                    (from_date.strftime(lang.date_format),
                     to_date.strftime(lang.date_format)))
                invoice_line_obj.create(invoice_line_vals)
            for consume_line in consume_lines.values():
                price = consume_line['price_unit']
                contract_obj._get_extra_values_invoice_line(
                    invoice_vals, consume_line)
                consume_line['price_unit'] = price
                consume_line['invoice_id'] = invoice.id
                consume_line['name'] += (
                    '\n' + _('Period: from %s to %s') %
                    (from_date.strftime(lang.date_format),
                     to_date.strftime(lang.date_format)))
                invoice_line_obj.create(consume_line)
        return True
