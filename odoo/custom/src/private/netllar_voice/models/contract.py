# -*- coding: utf-8 -*-
# Copyright 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2016-2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import _, api, fields, models
from openerp.exceptions import Warning as UserError
from datetime import timedelta
import datetime
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DSDTF
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DSDF

MINIMUM_PRICE_TO_INVOICE = 0.10


class Contract(models.Model):
    _inherit = 'sale.telecommunications.contract'

    @api.model
    def _apply_rules(self, contract_line, date, dest, apply_to,
                     apply_to_subtype, rule_type, bond_amount, quantity):
        """Browse corresponding rules to check if there is any that can be
        applied.
        @param date: Date of the call.
        @param apply_to: Type of the consume line to apply (call, SMS, MMS
          or data).
        @param apply_to_subtype: Subtype of the consume line to apply
          (domestic, roaming or EU).
        @param rule_type: Type of the rule to apply.
        @param bond_amount: Remaining bond amount (only for base calculation).
        @param quantity: Original length of the call/quantity of SMS/MMS or
        amount of data.
        @return: Resulting length/quantity/amount after applying rules.
        @attention: It's implied that rules are already pre-ordered by priority
        thanks to the '_order' variable on corresponding models.
        """
        if not quantity:
            return quantity
        rule_obj = self.env['sale.telecommunications.rule']
        bond = contract_line.bond_id
        res = quantity
        # Check bond rules and contract lines rules together
        rules = []
        rules.extend(bond.rule_lines)
        rules.extend(contract_line.rule_lines)
        for rule in rules:
            if (rule.type == rule_type and rule.apply_to == apply_to and
                    rule.apply_to_subtype == apply_to_subtype and
                    rule.isValid(rule, contract_line, date,
                                 dest_id=dest and dest.id or False)):
                if rule_type == 'base':
                    res = rule_obj._getCallLength(rule, bond_amount, res)
                elif rule_type == 'price':
                    res = rule_obj._getCallPrice(rule, res)
                elif rule_type == 'no_call_setup':
                    res = 0.0
                if res == 0.0:
                    break
        return res

    @api.multi
    def _calc_generic_price(self, cdr_line, max_allowed, pl_versions,
                            contract_line=None):
        """Calculate price for a CDR line.

        :param max_allowed: for franchise invoicing, this parameter is set to
          {} for invoicing everything.
        :param contract_line: if set, it means that calculation has to take
          in account modification rules (for normal invoicing). Otherwise,
          price calculation is set without rules (for franchise invoicing).
        """
        line_type = cdr_line.line_type
        line_subtype = cdr_line.line_subtype
        if cdr_line.caller_id.type == 'land':
            pll_obj = self.env['product.pricelist.voice_line']
        else:
            pll_obj = self.env['product.pricelist.mobile_line']
        bond_time = 0
        price = 0
        remaining_length = cdr_line.length
        groups = max_allowed.keys()
        # If there is a group with no prefix group, put this group the last one
        # to be the default rule
        if False in groups:
            groups.remove(False)
            groups.append(False)
        for group in groups:
            if not group or group.belongsTo(cdr_line.dest_id.id):
                bond_time = max_allowed[group]
                max_allowed[group] -= cdr_line.length
                if max_allowed[group] < 0:
                    remaining_length = -max_allowed[group]
                    del max_allowed[group]
                else:
                    remaining_length = 0
                break
        date = datetime.datetime.strptime(cdr_line.date, DSDTF)
        if contract_line:
            number_over = self._apply_rules(
                contract_line, date, cdr_line.dest_id, line_type, line_subtype,
                'base', bond_time, remaining_length,
            )
        else:
            number_over = remaining_length
        # Calculate price
        price_unit = 0
        pll_price = False
        if number_over or (line_type == 'call' and
                           remaining_length >= cdr_line.length):
            # Look for price for a specific prefix
            pll_price = pll_obj.search(
                [('version_id', '=', pl_versions.ids[0]),
                 ('prefix_id', '=', cdr_line.dest_id.id),
                 ('line_type', '=', line_type)])[:1]
            if not pll_price:
                # Look for unit price for a prefix group
                plls = pll_obj.search(
                    [('version_id', '=', pl_versions.ids[0]),
                     ('group_id', '!=', False),
                     ('line_type', '=', line_type)])
                for pll in plls:
                    if pll.group_id.belongsToGroup(pll.group_id,
                                                   cdr_line.dest_id.id):
                        pll_price = pll
                        break
        if number_over:
            if pll_price:
                if not pll_price.use_cost_price:
                    price_unit = pll_price.price
            else:
                pl = pl_versions[0]
                if line_type == 'sms':
                    price_unit = pl.sms_def_price
                elif line_type == 'mms':
                    price_unit = pl.mms_def_price
                elif line_type == 'data':
                    price_unit = pl.data_def_price
                elif line_subtype == 'call_roaming':
                    pass  # The calculation is done after
                else:
                    raise UserError(
                        _("Price for the prefix '%s' (%s) not found")
                        % (cdr_line.dest_id.prefix, cdr_line.dest_id.name))
            if pll_price.use_cost_price:
                price = cdr_line.cost * (
                    pll_price.sale_rate or
                    pll_price.version_id.default_sale_rate
                )
            elif line_subtype in ['data_roaming', 'sms_roaming',
                                  'mms_roaming', 'call_roaming']:
                price = cdr_line.cost * pl_versions[0].default_sale_rate
            elif line_type == 'call':
                price = price_unit / 60.0 * number_over
            elif line_type == 'data':
                price = price_unit / 1024.0 * number_over
            else:
                price = price_unit * number_over
            if contract_line:
                price = self._apply_rules(
                    contract_line, date, cdr_line.dest_id, line_type,
                    line_subtype, 'price', 0, price,
                )
        if (line_type == 'call' and remaining_length >= cdr_line.length and
                cdr_line.length and
                (pll_price and not pll_price.use_cost_price or not pll_price)):
            # Add call setup price because length is fully outside the bond
            # (ignoring rules discounts) only if use cost price is not marked
            if not pll_price:
                raise UserError(
                    _("Price for the prefix '%s' (%s) not found") %
                    (cdr_line.dest_id.prefix, cdr_line.dest_id.name)
                )
            if contract_line:
                price += self._apply_rules(
                    contract_line, date, cdr_line.dest_id, line_type,
                    line_subtype, 'no_call_setup', 0,
                    pll_price.call_setup_price,
                )
        return price

    @api.model
    def _process_consume_lines(self, contract_line, consume_lines):
        res = super(Contract, self)._process_consume_lines(
            contract_line, consume_lines)
        for cdr_line, price in consume_lines.iteritems():
            cdr_line.price = price
        return res

    @api.model
    def _add_invoice_lines_postpaid(
            self, contract_line, from_date, to_date, quota, invoice_vals,
            is_franchise=False):
        """Inherited method that is going to add lines for voice consumption.
        """
        if isinstance(from_date, datetime.date):
            from_date = datetime.datetime(
                year=from_date.year, month=from_date.month, day=from_date.day)
        if isinstance(to_date, datetime.date):
            to_date = datetime.datetime(
                year=to_date.year, month=to_date.month, day=to_date.day)
            to_date += timedelta(days=1) - timedelta(seconds=1)
        price_lines, invoice_lines = super(
            Contract, self)._add_invoice_lines_postpaid(
            contract_line, from_date, to_date, quota, invoice_vals,
            is_franchise=is_franchise)
        cdr_line_obj = self.env['sale.telecommunications.cdr.line']
        pl_vers_obj = self.env['product.pricelist.version']
        if not contract_line.cli_id:
            return price_lines, invoice_lines
        partner = self.env['res.partner'].browse(invoice_vals['partner_id'])
        domain = [('pricelist_id', '=', partner.property_product_pricelist.id),
                  '|',
                  ('date_start', '=', False),
                  ('date_start', '<=', invoice_vals['date_invoice']),
                  '|',
                  ('date_end', '=', False),
                  ('date_end', '>=', invoice_vals['date_invoice'])]
        domain_categ = list(domain)
        # TODO: Cambiar a multi-valor (category_ids)
        domain_categ.append(('category', '=',
                             contract_line.product_id.categ_id.id))
        pl_versions = pl_vers_obj.search(domain_categ)
        if not pl_versions:
            pl_versions = pl_vers_obj.search(domain)
        # Search for the events of this CLI in the time frame
        if contract_line.start_date:
            start_date = datetime.datetime.strptime(
                contract_line.start_date, DSDF)
            if start_date > from_date:
                from_date = start_date
        if contract_line.end_date:
            end_date = datetime.datetime.strptime(contract_line.end_date, DSDF)
            if end_date < to_date:
                to_date = end_date
        cdr_lines = cdr_line_obj.search(
            [('caller_id', '=', contract_line.cli_id.id),
             ('date', '>=', from_date.strftime(DSDTF)),
             ('date', '<=', to_date.strftime(DSDTF))])
        if not cdr_lines:
            return price_lines, invoice_lines
        bond = contract_line.bond_id
        # Buscar si tiene inhibido el usar bonos
        # TODO: Cambiar a multi-valor (category_ids)
        pl_items = self.env['product.pricelist.item'].search(
            [('price_version_id', 'in', pl_versions.ids),
             '|',
             ('product_id', '=', contract_line.product_id.id),
             ('categ_id', '=', contract_line.product_id.categ_id.id)])
        line_types = self.env['sale.telecommunications.cdr.line'].fields_get(
            allfields=['line_type']
        )['line_type']['selection']
        if pl_items and pl_items[0].no_bonds:
            max_allowed = {}
        else:
            max_allowed = bond.get_bond_max_allowed(quota)
        # Calculate prices
        prices = dict.fromkeys([x[0] for x in line_types], 0.0)
        for cdr_line in cdr_lines:
            max_type = max_allowed.get(cdr_line.line_type, {})
            # Get specific subtype limits or generic if not found
            max_subtype = max_type.get(
                cdr_line.line_subtype, max_type.get(False, {})
            )
            line_price = self._calc_generic_price(
                cdr_line, max_subtype, pl_versions,
                contract_line=contract_line,
            )
            price_lines[cdr_line] = line_price
            prices[cdr_line.line_type] += line_price
        # Exceeded prices for the full invoice
        for call_type, price in prices.iteritems():
            if price:
                if call_type == 'call':
                    product_id = bond.voice_exceeded_product_id.id
                    name = _("Exceeded seconds")
                elif call_type == 'sms':
                    product_id = bond.sms_exceeded_product_id.id
                    name = _("Exceeded SMS")
                elif call_type == 'mms':
                    product_id = bond.mms_exceeded_product_id.id
                    name = _("Exceeded MMS")
                elif call_type == 'data':
                    product_id = bond.data_exceeded_product_id.id
                    name = _("Exceeded data")
                else:
                    raise UserError(
                        "Tipo de llamada sin producto de sobretarificación "
                        "asociado: %s" % call_type)
                invoice_line_vals = {
                    'quantity': 1,
                    'product_id': product_id,
                }
                self._get_extra_values_invoice_line(
                    invoice_vals, invoice_line_vals)
                # Rewrite default values brought by last call
                invoice_line_vals['price_unit'] = price
                invoice_line_vals['name'] = (
                    "%s %s '%s'" % (
                        name, _('from'), contract_line.bond_id.name))
                invoice_lines.append(invoice_line_vals)
        return price_lines, invoice_lines

    @api.model
    def _invoice_created(self, invoiced_lines, invoice, cdr_lines=None):
        """Write references to the CDR lines corresponding to this invoice.
        This cannot be done on method '_add_invoice_lines_postpaid' because
        we don't know yet the invoice number.

        The CDR lines have been passed on context.
        """
        if cdr_lines:
            cdr_lines.write({'invoice_id': invoice.id})
        return super(Contract, self)._invoice_created(
            invoiced_lines, invoice, cdr_lines=cdr_lines
        )

    @api.model
    def make_invoices_planned(self):
        # TODO: Poner comprobación de que no hay ninguna excepción de
        # importación pendiente
        return super(Contract, self).make_invoices_planned()

    @api.model
    def _create_post_consume_invoice(self, contract, line, invoice_date):
        """Method for invoicing contract lines already finished."""
        if contract.company_id.partner_id.id == contract.partner_id.id:
            # No facturar auto-consumo
            return False
        invoice_obj = self.env['account.invoice']
        self_ctx = self.with_context(
            company_id=contract.company_id.id,
            force_company=contract.company_id.id, type='out_invoice')
        invoice_vals = self_ctx._prepare_invoice_vals(contract, invoice_date)
        from_date = datetime.datetime.strptime(line.last_invoice_date, DSDF)
        to_date = datetime.datetime(year=2999, month=12, day=31)
        price_lines, invoice_lines = self_ctx._add_invoice_lines_postpaid(
            line, from_date, to_date, 1.0, invoice_vals)
        for cdr_line, price in price_lines.iteritems():
            cdr_line.price = price
        if (invoice_lines and
                sum([x['price_unit'] for x in invoice_lines]) >
                MINIMUM_PRICE_TO_INVOICE):
            # Get lang record for format purposes
            lang_obj = self.env['res.lang']
            if contract.partner_id.lang:
                lang_code = contract.partner_id.lang
            elif self.env.context.get('lang'):
                lang_code = self.env.context['lang']
            else:
                lang_code = self.env.user.context_lang
            lang = lang_obj.search([('code', '=', lang_code)])
            # Add period to the first line (and possibly the only)
            to_date = datetime.datetime.strptime(line.end_date, DSDF)
            invoice_lines[0]['name'] += (
                _('Period: from %s to %s') % (
                    from_date.strftime(lang.date_format),
                    to_date.strftime(lang.date_format)))
            invoice_vals['invoice_line'] = [(0, 0, x) for x in invoice_lines]
            invoice = invoice_obj.create(invoice_vals)
            # Create invoice contract record
            self.env['sale.telecommunications.contract.invoice'].create(
                {'contract_id': contract.id,
                 'invoice_id': invoice.id})
            # Launch invoice created trigger
            cdr_lines = self.env['sale.telecommunications.cdr.line']
            for cdr_line in price_lines.keys():
                cdr_lines |= cdr_line
            self_ctx._invoice_created(line, invoice, cdr_lines=cdr_lines)
            invoice.signal_workflow('invoice_open')
            return invoice

    @api.multi
    def make_invoices(self):
        """Check if there is voice consume to invoice for lines that has ended
        in this period.
        """
        res = super(Contract, self).make_invoices()
        now = datetime.datetime.now()
        for contract in self:
            period_types = ('pre-paid', 'pre-paid-natural')
            if (not contract.active or
                    contract.period_type not in period_types):
                continue
            for line in contract.contract_line:
                if (not line.end_date or not line.product_id.bond_id or
                        not line.last_invoice_date):
                    # Descartar líneas que no han finalizado, o no son de
                    # telefonía, o no han emitido ninguna factura
                    continue
                if line.last_invoice_date < line.end_date:
                    date_diff = now - datetime.datetime.strptime(
                        line.end_date, DSDF)
                    if date_diff.days >= 2:
                        self._create_post_consume_invoice(
                            contract, line, now)
                        line.write({'last_invoice_date': now.strftime(DSDF)})
        return res


class ContractLine(models.Model):
    _inherit = 'sale.telecommunications.contract.line'

    cli_id = fields.Many2one(
        comodel_name='sale.telecommunications.cli', string='Associated CLI',
        copy=False)
    bond_id = fields.Many2one(
        related='product_id.bond_id', string="Bond", store=False,
        comodel_name='sale.telecommunications.bond', readonly=True)
    rule_lines = fields.One2many(
        comodel_name='sale.telecommunications.contract.line.rule',
        inverse_name='contract_line_id', string='Rule lines',
    )

    def _check_cli_assignation(self, cr, uid, ids, context=None):
        return True
        # Deshabilitado por el producto "Ampliación 500 MB"
        # for line in self.browse(cr, uid, ids, context=context):
        #     if line.cli_id:
        #         domain = [('id', '!=', line.id),
        #                   ('cli_id', '=', line.cli_id.id)]
        #         if line.start_date:
        #             domain.append('|')
        #             domain.append(('end_date', '>=', line.start_date))
        #             domain.append(('end_date', '=', False))
        #         if line.end_date:
        #             domain.append('|')
        #             domain.append(('start_date', '<=', line.end_date))
        #             domain.append(('start_date', '=', False))
        #         line_ids = self.search(cr, uid, domain, context=context)
        #         if line_ids:
        #             return False
        # return True

    _constraints = [
        (_check_cli_assignation,
         "El CLI ya está seleccionado en otra línea para el periodo "
         "establecido.", ['start_date', 'end_date', 'cli_id']),
    ]

    @api.model
    def create(self, vals):
        res = super(ContractLine, self).create(vals)
        if vals.get('cli_id'):
            self.env['sale.telecommunications.cli'].browse(
                vals['cli_id']).assigned = True
        return res

    @api.multi
    def write(self, vals):
        res = super(ContractLine, self).write(vals)
        if vals.get('cli_id'):
            self.env['sale.telecommunications.cli'].browse(
                vals['cli_id']).assigned = True
        return res

    @api.multi
    def onchange_product_id(self, product_id=False):
        result = super(ContractLine, self).onchange_product_id(
            product_id=product_id)
        if product_id:
            product = self.env['product.product'].browse(product_id)
            if product:
                result['value']['bond_id'] = product.bond_id.id
                if not product.bond_id:
                    result['value']['cli_id'] = False
        return result

    @api.model
    def _prepare_invoice_line_vals(self, invoice, quota, lang):
        """Inherited method that adds bond concepts on invoice line."""
        line_vals = super(ContractLine, self)._prepare_invoice_line_vals(
            invoice, quota, lang,
        )
        if self.cli_id:
            line_vals['name'] += u"\nNº asociado: %s" % self.cli_id.name
        rules = []
        if self.bond_id:
            rules.extend(self.bond_id.rule_lines)
        rules.extend(self.rule_lines)
        for rule in rules:
            if rule.isValid(rule, self, quota['real_start_date'],
                            quota['real_end_date']):
                line_vals['name'] += '\n%s' % rule.name
        return line_vals
