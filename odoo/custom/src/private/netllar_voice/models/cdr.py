# -*- coding: utf-8 -*-
# Copyright 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2016-2017 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, exceptions, fields, models, _
from pytz import timezone, utc
from openerp.addons.decimal_precision import decimal_precision as dp

CDR_LINE_UNIQUE_FIELDS = ['date', 'caller_id', 'dest', 'length', 'line_type']


class Cdr(models.Model):
    _name = "sale.telecommunications.cdr"
    _description = "Call Detail Record (CDR)"
    _order = 'date desc'

    @api.multi
    def name_get(self):
        res = []
        for cdr in self:
            if self.env.context.get('tz'):
                # Process time in local timezone
                date = fields.Datetime.from_string(cdr.date)
                local_tz = timezone(self.env.context['tz'])
                date = utc.localize(date)
                date = date.astimezone(local_tz)
                date = fields.Datetime.to_string(date)
            else:
                date = cdr.date
            res.append((cdr.id, "%s (%s) - %s" % (
                date, cdr.import_type, cdr.name)))
        return res

    @api.multi
    def button_unlink(self):
        self.unlink()

    name = fields.Char(default="Import")
    import_type = fields.Selection(
        related="profile_id.import_type", store=True, index=True,
        readonly=True)
    date = fields.Datetime(string='Import date', required=True, index=True)
    profile_id = fields.Many2one(
        comodel_name='sale.telecommunications.import.profile',
        string='Profile reference')
    line_ids = fields.One2many(
        comodel_name='sale.telecommunications.cdr.line', inverse_name='cdr_id',
        string='CDR lines')
    exception_ids = fields.One2many(
        comodel_name='sale.telecommunications.import.exception',
        inverse_name='cdr_id', string='Exception lines')


class CdrLine(models.Model):
    _name = "sale.telecommunications.cdr.line"
    _description = "Call Detail Record (CDR) line"
    _rec_name = 'date'
    _order = 'date'

    cdr_id = fields.Many2one(
        comodel_name='sale.telecommunications.cdr', string='CDR reference',
        required=True, ondelete="cascade")
    invoice_id = fields.Many2one(
        comodel_name='account.invoice', string='Invoice reference')
    caller_id = fields.Many2one(
        comodel_name='sale.telecommunications.cli', string='Source CLI',
        required=True, index=True)
    company_id = fields.Many2one(
        comodel_name="res.company", related='caller_id.company_id',
        string='Company', store=True, readonly=True,
    )
    profile_id = fields.Many2one(
        related='cdr_id.profile_id', string='Profile', readonly=True,
        comodel_name="sale.telecommunications.import.profile", store=True)
    line_type = fields.Selection(
        selection=[
            ('call', 'Call'),
            ('sms', 'SMS'),
            ('mms', 'MMS'),
            ('data', 'Data'),
        ], string='Type', required=True, default='call',
    )
    line_subtype = fields.Selection(
        selection=[
            ('domestic', 'Domestic'),
            ('roaming', 'Roaming'),
            ('eu', 'EU'),
        ], default='domestic', string="Subtype", required=True,
    )
    date = fields.Datetime(
        string='Call date', required=True, index=True)
    dest = fields.Char(string='Destination number', size=30)
    dest_id = fields.Many2one(
        comodel_name='sale.telecommunications.prefix',
        string='Destination prefix', index=True)
    length = fields.Integer(
        string='Amount', required=True, group_operator="sum",
        help="Amount of the event (seconds for calls, KB for data and number "
             "for messages")
    prefix = fields.Char(size=30)
    price = fields.Float(
        string='Sale price', digits_compute=dp.get_precision('Voice price'),
        help="This is the price at which the line is going to be sold. This "
             "will be 0 in two cases: a) It hasn't been calculated; b) The "
             "call is still inside the max minutes in the bond. WARNING: This "
             "field is calculated in the generation of the invoices process.",
        readonly=True)
    cost = fields.Float(
        string='Cost price', digits_compute=dp.get_precision('Voice price'))
    comment = fields.Char(string='Additional comments', size=200)

    @api.multi
    def _is_duplicated(self, vals):
        domain = [(x, '=', vals.get(x, False)) for x in CDR_LINE_UNIQUE_FIELDS]
        if self:
            domain.append(('id', '!=', self.id))
        line_ids = self.search(domain)
        return bool(line_ids)

    @api.multi
    @api.constrains(*CDR_LINE_UNIQUE_FIELDS)
    def _check_unique(self):
        if self.env.context.get('no_constraint'):
            return
        for line in self:
            vals = self._convert_to_write(line._cache)
            if line._is_duplicated(vals):
                raise exceptions.ValidationError(
                    _("Combination not unique (%s).") %
                    ", ".join(vals.get(x)) for x in CDR_LINE_UNIQUE_FIELDS)

    @api.model
    def _prepare_cdr_line(self, vals, company_id=None):
        cli_obj = self.env["sale.telecommunications.cli"].sudo().with_context(
            active_test=False,
        )
        prefix_obj = self.env["sale.telecommunications.prefix"]
        # Caller ID check (for all types)
        if not vals.get('caller_id'):
            cli = cli_obj.search([('name', '=', vals['caller'])], limit=1)
            if cli:
                vals['caller_id'] = cli.id
            else:
                # Auto-create CLI
                if not company_id:
                    raise exceptions.Warning(
                        _('Company not provided auto-creating the CLI'))
                cli_obj = self.env['sale.telecommunications.cli']
                vals['caller_id'] = cli_obj.create({
                    'name': vals['caller'],
                    'type': cli_obj._get_type_from_cli(vals['caller']),
                    'company_id': company_id,
                }).id
        cli = cli_obj.browse(vals['caller_id'])
        vals['company_id'] = cli.company_id.id
        # TODO: Don't check global wildcard CLIs
        if not cli.contract_line_id:
            vals['type'] = 'cli_unassigned'
        # Destination check (for calls and SMS/MMS)
        if vals['line_type'] not in ('data', 'data_roaming'):
            if not vals.get('dest_id'):
                # Try first only with the prefix
                prefixes = False
                if vals.get('prefix'):
                    prefixes = prefix_obj.search(
                        [('prefix', '=', vals['prefix'])])
                # If not, select all prefixes
                if not prefixes:
                    prefixes = prefix_obj.search([])
                dest_prefix = False
                for prefix in prefixes:
                    if vals['dest'].startswith(prefix.prefix):
                        if not dest_prefix or (len(prefix.prefix) >
                                               len(dest_prefix.prefix)):
                            dest_prefix = prefix
                if dest_prefix:
                    vals['dest_id'] = dest_prefix.id
                else:
                    vals['type'] = 'prefix_not_found'
        return vals
