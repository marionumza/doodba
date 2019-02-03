# -*- coding: utf-8 -*-
# Copyright 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import _, api, fields, exceptions, models
from datetime import timedelta
import datetime
from dateutil.relativedelta import relativedelta
from openerp.tools import config
import openerp.addons.decimal_precision as dp
import calendar
import logging

_logger = logging.getLogger(__name__)

try:
    from openerp.addons.connector.queue.job import job
    from openerp.addons.connector.session import ConnectorSession
except ImportError:
    _logger.debug('Can not `import connector`.')
    import functools

    def empty_decorator_factory(*argv, **kwargs):
        return functools.partial
    job = empty_decorator_factory


class Contract(models.Model):
    _name = 'sale.telecommunications.contract'

    def _get_next_term_date(self, date, unit, interval):
        """Get the date that results on incrementing given date an interval of
        time in time unit.

        @param date: Original date.
        @param unit: Interval time unit.
        @param interval: Quantity of the time unit.
        @rtype: date
        @return: The date incremented in 'interval' units of 'unit'.
        """
        if unit == 'days':
            return date + timedelta(days=interval)
        elif unit == 'weeks':
            return date + timedelta(weeks=interval)
        elif unit == 'months':
            return date + relativedelta(months=interval)
        elif unit == 'years':
            return date + relativedelta(years=interval)

    def _get_previous_term_date(self, date, unit, interval):
        """Get the date that results on decrementing given date an interval of
        time in time unit.

        @param date: Original date.
        @param unit: Interval time unit.
        @param interval: Quantity of the time unit.
        @rtype: date
        @return: The date decremented in 'interval' units of 'unit'.
        """
        if unit == 'days':
            return date - timedelta(days=interval)
        elif unit == 'weeks':
            return date - timedelta(weeks=interval)
        elif unit == 'months':
            return date - relativedelta(months=interval)
        elif unit == 'years':
            return date - relativedelta(years=interval)

    @api.multi
    @api.depends('prolong', 'prolong_interval', 'prolong_unit', 'end_date')
    def _compute_next_expiration_date(self):
        for contract in self:
            if contract.prolong == 'fixed':
                contract.next_expiration_date = contract.end_date
            elif contract.prolong == 'unlimited':
                now = datetime.date.today()
                expiration_date = fields.Date.from_string(
                    contract.start_date or fields.Date.today())
                while expiration_date < now:
                    expiration_date = self._get_next_term_date(
                        expiration_date, contract.prolong_unit,
                        contract.prolong_interval)
                contract.next_expiration_date = fields.Date.to_string(
                    expiration_date)

    name = fields.Char(
        string='Name', index=True, required=True,
        help='Name that helps to identify the contract')
    number = fields.Char(
        'Contract number', index=True, size=32, copy=False,
        help="Number of contract. Keep empty to get the number assigned "
             "by a sequence.")
    active = fields.Boolean(
        string='Active', default=True, copy=False,
        help='Unchecking this field, quotas are not generated')
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Customer', index=True,
        change_default=True, required=True,
        help="Customer you are making the contract with")
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', required=True,
        help="Company that signs the contract", index=True,
        default=lambda self: self.env['res.company']._company_default_get(
            'account'))
    journal_id = fields.Many2one(
        comodel_name='account.journal', string='Journal',
        required=True, help="Journal where invoices are going to be created")
    start_date = fields.Date(
        string='Start date', index=True, required=True, copy=False,
        help="Beginning of the contract. Keep empty to use the current date")
    prolong = fields.Selection(
        selection=[
            ('unlimited', 'Unlimited term'),
            ('fixed', 'Fixed term')
        ],
        string='Prolongation', default='unlimited',
        help="Sets the term of the contract. 'Renewable fixed term': It "
             "sets a fixed term, but with possibility of manual renew; "
             "'Unlimited term': Renew is made automatically; 'Fixed "
             "term': The term is fixed and there is no possibility to "
             "renew.", required=True)
    end_date = fields.Date(string='End date', help="End date of the contract")
    invoicing_day = fields.Integer(
        string='Invoicing day', default=1,
        help="Day of month to invoice the contract. Leave it blank to "
             "invoice on its natural period day.")
    prolong_interval = fields.Integer(
        string='Interval', default=1,
        help="Interval in time units to prolong the contract until new "
             "renewall (that is automatic for unlimited term, manual for "
             "renewable fixed term).")
    prolong_unit = fields.Selection(
        selection=[('days', 'days'),
                   ('weeks', 'weeks'),
                   ('months', 'months'),
                   ('years', 'years')],
        string='Interval unit', default='years',
        help='Time unit for the prolongation interval')
    contract_line = fields.One2many(
        comodel_name='sale.telecommunications.contract.line',
        inverse_name='contract_id', string='Contract lines', copy=True,
    )
    invoice_line = fields.One2many(
        comodel_name='sale.telecommunications.contract.invoice',
        inverse_name='contract_id', string='Generated invoices', readonly=True)
    last_renovation_date = fields.Date(
        string='Last renovation date',
        help="Last date when contract was renewed (same as start date if "
             "not renewed)")
    next_expiration_date = fields.Date(
        compute='_compute_next_expiration_date', string='Next expiration date',
        store=True)
    period_type = fields.Selection(
        selection=[('pre-paid', 'Pre-paid'),
                   ('post-paid', 'Post-paid'),
                   ('pre-paid-natural', 'Pre-paid - Natural month'),
                   ('post-paid-natural', 'Post-paid - Natural month')],
        string="Period type", required=True, default='pre-paid',
        help="Period type for invoicing.\n"
             "Pre-paid': Invoices are generated for the upcoming period.\n"
             "Post-paid': Invoices are generated for the consumed period.\n"
             "Pre-paid - Natural month': Invoices are generated for the "
             "upcoming period, using natural months for the period.\n"
             "Post-paid - Natural month': Invoices are generated for the "
             "consumed period, using natural months for the period. ")
    state = fields.Selection(
        selection=[('empty', 'Without invoices'),
                   ('first', 'First invoice created'),
                   ('invoices', 'With invoices')],
        string='State', readonly=True, default='empty')
    notes = fields.Text('Notes')

    @api.multi
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Check correct dates. When prolongation is unlimited or renewal,
        end_date is False, so doesn't apply.
        """
        for contract in self:
            if contract.end_date and contract.end_date > contract.start_date:
                raise exceptions.ValidationError(
                    _('Contract end date must be greater than start date'),
                )

    @api.multi
    @api.constrains('contract_line', 'start_date')
    def _check_line_dates(self):
        """Check correct dates. When prolongation is unlimited or renewal,
        end_date is False, so doesn't apply
        """
        for line in self.mapped('contract_line').filtered('start_date'):
            if line.start_date < line.contract_id.start_date:
                raise exceptions.ValidationError(
                    _('Contract start date must be smaller or equal than '
                      'lines start date'),
                )

    @api.model
    def create(self, vals):
        """Set start date or number if empty."""
        if not vals.get('start_date'):
            vals['start_date'] = fields.Date.today()
        if not vals.get('number'):
            vals['number'] = self.env['ir.sequence'].next_by_code(
                'sale.tc.sequence'
            )
        return super(Contract, self).create(vals)

    @api.multi
    def write(self, vals):
        """Change day of last invoice if we are changing the invoicing day.
        This is for avoiding errors on periods computations."""
        invoicing_day = self.invoicing_day
        res = super(Contract, self).write(vals)
        if not vals.get('invoicing_day'):
            return res
        for line in self.mapped('contract_line').filtered('last_invoice_date'):
            if int(line.last_invoice_date[-2:]) == invoicing_day:
                new_date = fields.Date.from_string(
                    line.last_invoice_date
                ).replace(day=vals['invoicing_day'])
                line.write({
                    'last_invoice_date': fields.Date.to_string(new_date),
                })
        return res

    @api.multi
    def copy(self, default=None):
        if default is None:
            default = {}
        default.update({
            'state': 'empty',
            'name': '%s*' % self.name,
        })
        return super(Contract, self).copy(default=default)

    @api.onchange('start_date')
    def onchange_start_date(self):
        """It changes last renovation date to the new start date."""
        if not self.start_date:
            return
        self.last_renovation_date = self.start_date

    @api.model
    def _invoice_created(self, lines_invoiced, invoice, cdr_lines=None):
        """It triggers actions after invoice is created. This method can be
        overrode for extending its functionality thanks to its parameters, for
        example for e-mail notification.
        """
        _logger.info(
            "Invoice %s created from contract %s", invoice.id, self.id
        )

    def _substract_working_days(self, date, days):
        """Substract to the given date the number of working days indicated.
        Working days are supposed to be from monday to friday.
        """
        result = date - timedelta(days=days)
        if days > 0:
            if result.weekday() == 5:
                result -= timedelta(days=1)  # It's saturday
            elif result.weekday() == 6:
                result -= timedelta(days=2)  # It's sunday
        return result

    def _add_working_days(self, date, days):
        """Add to the given date the number of working days indicated.
        Working days are supposed to be from monday to friday.
        """
        addDays = days
        if date.weekday() == 4:  # It's friday
            addDays += 2
        return date + timedelta(days=addDays)

    @api.model
    def send_error_mail(self, errors):
        user = self.env.user
        if not user.email:
            return
        body = (
            u"Se han producido los siguientes errores en la generación de "
            u"facturas del día %s:<br><br>\n\n" % fields.Date.today())
        for contract, error in errors:
            if contract:
                body += u"<u>Contrato nº</u>: <b>%s</b> (ID: %s)<br>\n" % (
                    contract.number, contract.id)
            body += u"<u>Error</u>: %s<br><br>\n\n" % error
        mail_vals = {
            'email_to': user.email,
            'recipient_ids': [(6, 0, user.partner_id.ids)],
            'body_html': body,
            'email_from': 'netllar@netllar.es',
            'subject': u"[OpenERP] Errores en la generación de facturas",
        }
        mail = self.env['mail.mail'].create(mail_vals)
        mail.send()

    def _is_contract_line_invoiceable(self, contract_line, date,
                                      invoice_date):
        """Determines if a contract line is invoiceable in the moment set by
        'date' variable for the invoice date given.
        """
        next_process_date = self._substract_working_days(
            invoice_date,
            contract_line.contract_id.journal_id.anticipation_days,
        )
        if next_process_date > date:
            return False
        from_date, to_date = contract_line._get_date_interval(invoice_date)
        invoiceable = True
        if contract_line.start_date:
            start_date = fields.Date.from_string(contract_line.start_date)
            invoiceable &= (start_date <= to_date)
        if contract_line.end_date:
            end_date = fields.Date.from_string(contract_line.end_date)
            invoiceable &= (end_date >= from_date)
        return invoiceable

    @api.model
    def make_invoices_planned(self):
        """Cron for invoicing pending contracts."""
        self.search([]).make_invoices()
        return True

    @api.multi
    def make_invoices(self):
        """Check if there is any pending invoice to create from given
        contracts.
        """
        now = datetime.date.today()
        for contract in self:
            # No facturar contratos no activos o que sean de auto-consumo
            if (not contract.active or
                    contract.company_id.partner_id == contract.partner_id):
                continue
            compare_date = self._add_working_days(
                now, contract.journal_id.anticipation_days,
            )
            start_date = fields.Date.from_string(contract.start_date)
            expir_date = fields.Date.from_string(contract.next_expiration_date)
            if (start_date > compare_date or
                    (contract.prolong != 'unlimited' and
                     compare_date > expir_date)):
                continue
            lines_to_invoice = {}
            # Check if there is any contract line to invoice
            for line in contract.contract_line:
                next_invoice_date = line._get_next_invoice_date()
                if self._is_contract_line_invoiceable(
                        line, datetime.date.today(), next_invoice_date):
                    # Add to a dictionary to invoice all lines together
                    lines_to_invoice[line.id] = next_invoice_date
            if lines_to_invoice:
                ctx = self.env.context.copy()
                ctx['company_id'] = contract.company_id.id
                session = ConnectorSession.from_env(self.env(context=ctx))
                if not config['test_enable']:
                    create_invoice.delay(
                        session, contract._name, contract.id, lines_to_invoice,
                    )
                    # commit transaction to get immediate results
                    self.env.cr.commit()  # pylint: disable=E8102
                else:
                    create_invoice(
                        session, contract._name, contract.id, lines_to_invoice,
                    )
        return {}

    @api.model
    def _add_invoice_lines_postpaid(self, contract_line, from_date, to_date,
                                    quota, invoice, is_franchise=False):
        """Inheritable method for adding additional invoice lines to each
        contract line that corresponds to post-paid. Used in module
        netllar_voice for adding voice costs.

        :return A dictionary with CDR lines IDs as keys and prices as values,
            and a list with invoice lines dictionaries ready to be added to one
            invoice.
        """
        return {}, []

    def _process_consume_lines(self, contract_line, consume_lines):
        """Method for making another operations with consume lines when
        invoicing the regular way, because _add_invoice_lines_postpaid is used
        by several invoicing methods: regular, 'post-mortem' invoicing and
        franchise invoicing."""
        return

    def _add_invoice_lines_prepaid(self, contract_line, from_date, to_date,
                                   quota, invoice):
        """Inheritable method for adding additional invoice lines to each
        contract line that corresponds to pre-paid. Not used by now.
        """
        return []

    @api.multi
    def _prepare_invoice_vals(self, invoice_date):
        self.ensure_one()
        # This ensures that the properties are fetched for the correct company
        invoice_model = self.env['account.invoice'].with_context(
            force_company=self.company_id.id, type='out_invoice',
        )
        invoice = invoice_model.new({
            'date_invoice': fields.Date.to_string(invoice_date),
            'origin': self.number,
            'partner_id': self.partner_id.id,
            'journal_id': self.journal_id.id,
            'type': 'out_invoice',
            'currency_id': self.company_id.currency_id.id,
            'company_id': self.company_id.id,
            'internal_number': False,
            'user_id': self.partner_id.user_id.id,
        })
        invoice._onchange_partner_id()
        return invoice._convert_to_write(invoice._cache)

    def _get_invoice_date(self, contract_lines):
        journal_obj = self.env['account.journal']
        # Look for the greater date of the invoice lines
        invoice_date = datetime.date.min
        for line_date in contract_lines.values():
            if line_date > invoice_date:
                invoice_date = line_date
        # Search all journals that use the same sequence
        journals = journal_obj.search([
            ('invoice_sequence_id', '=',
             self.journal_id.invoice_sequence_id.id)
        ])
        # Check if date is lower than the last invoice date in that journals
        self.env.cr.execute(
            """SELECT MAX(date_invoice)
            FROM account_invoice
            WHERE journal_id IN %s AND state IN %s""",
            (tuple(journals.ids), ('open', 'paid')),
        )
        max_invoice = self.env.cr.fetchall()
        if max_invoice and max_invoice[0] and max_invoice[0][0]:
            max_invoice = fields.Date.from_string(max_invoice[0][0])
            if max_invoice > invoice_date:
                invoice_date = max_invoice
        now = datetime.date.today()
        if invoice_date < now:
            invoice_date = now
        return invoice_date


@job(default_channel='root.netllar_contract_invoicing')
def create_invoice(session, model_name, contract_id, contract_lines):
    """Method that creates an invoice from given data.
    @param contract: contract from which invoice is going to be generated.
    @param contract_lines: Dictionary with contract lines as keys and next
        invoice date of that line as values.
    """
    contract_obj = session.env[model_name]
    invoice_obj = session.env['account.invoice']
    inv_line_obj = session.env['account.invoice.line']
    contract_line_obj = session.env['sale.telecommunications.contract.line']
    contract_inv_obj = session.env['sale.telecommunications.contract.invoice']
    contract = contract_obj.browse(contract_id)
    # Get lang record for format purposes
    lang_obj = session.env['res.lang']
    if contract.partner_id.lang:
        lang_code = contract.partner_id.lang
    elif contract.env.context.get('lang'):
        lang_code = contract.env.context['lang']
    else:
        lang_code = contract.env.user.lang or 'en_US'
    lang = lang_obj.search([('code', '=', lang_code)], limit=1)
    # Create invoice header
    invoice_date = contract._get_invoice_date(contract_lines)
    invoice = invoice_obj.create(contract._prepare_invoice_vals(invoice_date))
    # Create invoice lines objects
    cdr_lines = None
    for contract_line_id in contract_lines.keys():
        line_date = contract_lines[contract_line_id]
        contract_line = contract_line_obj.browse(contract_line_id)
        quota = contract_line._get_quota(line_date)
        inv_line_obj.create(contract_line._prepare_invoice_line_vals(
            invoice, quota, lang,
        ))
        # Get other possible invoice lines derived from this contract line
        additional_lines = contract._add_invoice_lines_prepaid(
            contract_line, quota['real_start_date'],
            quota['real_end_date'], quota['quota'], invoice,
        )
        for additional_line in additional_lines:
            inv_line_obj.create(additional_line)
        if contract.period_type == 'pre-paid':
            period_type = 'post-paid'
        elif contract.period_type == 'pre-paid-natural':
            period_type = 'post-paid-natural'
        else:
            period_type = contract.period_type
        from_date_post, to_date_post = contract_line._get_date_interval(
            line_date, period_type=period_type,
        )
        consume_lines, additional_lines = contract._add_invoice_lines_postpaid(
            contract_line, from_date_post, to_date_post,
            quota['quota'], invoice
        )
        # HACK: Populate here CDR lines, although they're filled by
        # netllar_voice module
        for cdr_line in consume_lines.keys():
            if cdr_lines is None:
                cdr_lines = cdr_line
            else:
                cdr_lines |= cdr_line
        contract._process_consume_lines(contract_line, consume_lines)
        for additional_line in additional_lines:
            inv_line_obj.create(additional_line)
        contract_line.last_invoice_date = fields.Date.to_string(line_date)
    if contract.state != 'invoices':
        contract.state = 'invoices'
    # TODO: Replace by a one2many
    contract_inv_obj.create({
        'contract_id': contract.id,
        'invoice_id': invoice.id,
    })
    contract._invoice_created(contract_lines, invoice, cdr_lines=cdr_lines)
    # Confirm invoice - To be changed in v10
    invoice.signal_workflow('invoice_open')


class ContractLine(models.Model):
    _name = 'sale.telecommunications.contract.line'

    start_date = fields.Date(
        string='Start date', index=True, copy=False,
        help="Beginning of the contract line. Keep empty for no checking.")
    end_date = fields.Date(
        string='End date', index=True,
        help="End of the contract line. Keep empty for no checking.")
    contract_id = fields.Many2one(
        comodel_name='sale.telecommunications.contract', copy=False,
        string='Contract reference', ondelete='cascade')
    product_id = fields.Many2one(
        comodel_name='product.product', string='Product', ondelete='set null',
        required=True)
    name = fields.Char(
        related='product_id.name', string='Description',
        help='Product description', store=False)
    additional_description = fields.Char(
        string='Add. description', size=300,
        help="Additional description that will be added as invoice lines "
             "notes")
    quantity = fields.Float(
        string='Product quantity', required=True, default=1.0,
        help='Quantity of the product to invoice')
    discount = fields.Float('Discount (%)', digits=(16, 2))
    price = fields.Float(
        string='Specific price', digits_compute=dp.get_precision('Account'),
        help="Specific price for this product. Keep empty to use the list "
             "price while generating invoice")
    list_price = fields.Float(
        related='product_id.list_price', string="List price", store=False,
        readonly=True)
    invoicing_interval = fields.Integer(
        string='Invoicing interval', required=True, default=1,
        help="Interval in time units for invoicing this product")
    invoicing_unit = fields.Selection(
        selection=[('days', 'days'),
                   ('weeks', 'weeks'),
                   ('months', 'months'),
                   ('years', 'years')],
        string='Invoicing interval unit', required=True, default='months')
    last_invoice_date = fields.Date('Last invoice date', copy=False)
    notes = fields.Char('Notes')

    _sql_constraints = [
        ('line_qty_zero', 'CHECK (quantity > 0)',
            'All product quantities must be greater than 0.\n'),
        ('line_interval_zero', 'CHECK (invoicing_interval > 0)',
            'All invoicing intervals must be greater than 0.\n'),
    ]

    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return
        self.update({
            'name': self.product_id.name,
            'list_price': self.product_id.list_price,

        })

    @api.multi
    def _get_date_interval(self, date, period_type=None):
        """Calculates the period applying the contract line parameters for the
        date given.
        """
        self.ensure_one()
        contract = self.contract_id
        if not period_type:
            period_type = contract.period_type
        if period_type == 'pre-paid':
            from_date = date
            if not self.last_invoice_date:
                # Special case, first invoice
                if self.start_date:
                    start_date = fields.Date.from_string(self.start_date)
                else:
                    start_date = fields.Date.from_string(contract.start_date)
                if start_date < date:
                    from_date = contract._get_previous_term_date(
                        date, self.invoicing_unit, self.invoicing_interval)
            to_date = contract._get_next_term_date(
                from_date, self.invoicing_unit, self.invoicing_interval)
            to_date -= timedelta(days=1)
        elif period_type == 'pre-paid-natural':
            if self.invoicing_unit == 'days':
                from_date = date
            elif self.invoicing_unit == 'weeks':
                from_date = (date - timedelta(date.weekday()))
            elif self.invoicing_unit == 'months':
                from_date = datetime.date(
                    year=date.year, month=date.month, day=1
                )
            elif self.invoicing_unit == 'years':
                from_date = datetime.date(year=date.year, month=1, day=1)
            else:
                raise Exception('Invalid invoicing unit')
            to_date = contract._get_next_term_date(
                from_date, self.invoicing_unit, self.invoicing_interval)
            to_date -= timedelta(days=1)
        elif period_type == 'post-paid':
            to_date = date - timedelta(days=1)
            from_date = contract._get_previous_term_date(
                to_date, self.invoicing_unit, self.invoicing_interval)
            from_date += timedelta(days=1)
        elif period_type == 'post-paid-natural':
            if self.invoicing_unit == 'days':
                to_date = date - timedelta(days=1)
                from_date = contract._get_previous_term_date(
                    to_date, self.invoicing_unit, self.invoicing_interval)
            elif self.invoicing_unit == 'weeks':
                date -= timedelta(7)
                from_date = (date - timedelta(date.weekday()))
                to_date = (date + timedelta(6 - date.weekday()))
            elif self.invoicing_unit == 'months':
                date -= relativedelta(months=1)
                from_date = datetime.date(
                    year=date.year, month=date.month, day=1,
                )
                last_month_day = calendar.monthrange(date.year, date.month)[1]
                to_date = datetime.date(
                    year=date.year, month=date.month, day=last_month_day,
                )
            elif self.invoicing_unit == 'years':
                date -= relativedelta(years=1)
                from_date = datetime.date(year=date.year, month=1, day=1)
                to_date = datetime.date(year=date.year, month=12, day=31)
        return (from_date, to_date)

    @api.multi
    def _get_quota(self, date, period_type=None):
        self.ensure_one()
        from_date, to_date = self._get_date_interval(
            date, period_type=period_type)
        res = {
            'theoretical_start_date': from_date,
            'theoretical_end_date': to_date,
            'theoretical_length': (to_date - from_date).days + 1,
        }
        # Adjust result if line starts or ends in the middle of the period
        contract_start_date = fields.Date.from_string(
            self.contract_id.start_date)
        if contract_start_date > from_date:
            from_date = contract_start_date
        if self.start_date:
            start_date = fields.Date.from_string(self.start_date)
            if start_date > from_date:
                from_date = start_date
        if self.end_date:
            end_date = fields.Date.from_string(self.end_date)
            if end_date < to_date:
                to_date = end_date
        res['real_start_date'] = from_date
        res['real_end_date'] = to_date
        res['real_length'] = (to_date - from_date).days + 1
        res['quota'] = round(
            res['real_length'] / float(res['theoretical_length']), 2
        )
        return res

    def _get_correct_date(self, year, month, day):
        """Comprueba que la fecha a construir va a ser correcta."""
        month_last_day = calendar.monthrange(year, month)[1]
        if day > month_last_day:
            return datetime.date(year=year, month=month, day=month_last_day)
        else:
            return datetime.date(year=year, month=month, day=day)

    def _get_next_invoice_date(self):
        """Get next date when an invoice has to been generated for an contract
        line, starting from given date. It includes possible defined invoicing
        days.

        @param self: contract line.
        @rtype: datetime.
        @return: Next invoice date starting from the given date.
        """
        self.ensure_one()
        contract = self.contract_id
        if self.start_date:
            next_date = fields.Date.from_string(self.start_date)
        else:
            next_date = fields.Date.from_string(contract.start_date)
        last_date = (
            self.last_invoice_date and
            fields.Date.from_string(self.last_invoice_date) or False
        )
        if contract.period_type == 'post-paid-natural':
            if next_date.month == 12:
                next_date = self._get_correct_date(next_date.year + 1, 1, 1)
            else:
                next_date = self._get_correct_date(
                    next_date.year, next_date.month + 1, 1,
                )
        elif contract.period_type == 'post-paid':
            next_date = self._get_next_term_date(
                next_date, self.invoicing_unit, 1)
        elif contract.invoicing_day:
            if contract.period_type == 'pre-paid':
                # Special case
                if contract.invoicing_day <= next_date.day:
                    next_date = self._get_correct_date(
                        next_date.year, next_date.month,
                        contract.invoicing_day)
                else:
                    if next_date.month == 1:
                        next_date = self._get_correct_date(
                            next_date.year - 1, 12, contract.invoicing_day)
                    else:
                        next_date = self._get_correct_date(
                            next_date.year, next_date.month - 1,
                            contract.invoicing_day)
            else:
                if not last_date or contract.invoicing_day >= next_date.day:
                    next_date = self._get_correct_date(
                        next_date.year, next_date.month,
                        contract.invoicing_day)
                else:
                    if next_date.month == 12:
                        next_date = self._get_correct_date(
                            next_date.year + 1, 1, contract.invoicing_day)
                    else:
                        next_date = self._get_correct_date(
                            next_date.year, next_date.month + 1,
                            contract.invoicing_day)
        if last_date:
            while next_date <= last_date:
                next_date = self._get_next_term_date(
                    next_date, self.invoicing_unit, self.invoicing_interval)
        return next_date

    @api.multi
    def _prepare_invoice_line_vals(self, invoice, quota, lang):
        dpa = self.env['decimal.precision'].precision_get('Account')
        self.ensure_one()
        # TODO: Ver cómo hacer el nuevo account_invoice_pricelist
        line_obj = self.env['account.invoice.line'].with_context(
            force_company=self.contract_id.company_id.id, type='out_invoice',
            # pricelist_id=invoice.pricelist_id,
        )
        line = line_obj.new({
            'product_id': self.product_id.id,
            'quantity': round(self.quantity * quota['quota'], dpa),
            'discount': self.discount,
            'invoice_id': invoice.id,
        })
        line._onchange_product_id()
        if self.price:
            line.price_unit = self.price
        if self.additional_description:
            line.name += "\n" + self.additional_description
        line.name += (
            "\n" + _('Period: from %s to %s') %
            (quota['real_start_date'].strftime(lang.date_format),
             quota['real_end_date'].strftime(lang.date_format))
        )
        return line._convert_to_write(line._cache)


class ContractInvoice(models.Model):
    """Class for recording each invoice created for each line of the contract.
    It keeps only reference to the contract, not to the line.
    """
    _name = 'sale.telecommunications.contract.invoice'
    _rec_name = "invoice_id"

    contract_id = fields.Many2one(
        comodel_name='sale.telecommunications.contract',
        string='Contract reference', ondelete='cascade')
    date = fields.Date(
        related='invoice_id.date_invoice', string="Date of invoice creation",
        store=False)
    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Invoice', ondelete='cascade')

    @api.multi
    def view_invoice(self):
        """Method for viewing invoice associated to an contract."""
        self.ensure_one()
        view = self.env.ref('account.invoice_form')
        return {
            'domain': [('id', '=', self.invoice_id.id)],
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'context': self.env.context,
            'res_id': self.invoice_id.id,
            'view_id': view.ids,
            'type': 'ir.actions.act_window',
            'nodestroy': True
        }
