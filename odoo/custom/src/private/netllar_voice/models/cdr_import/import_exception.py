# -*- coding: utf-8 -*-
# © 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
import openerp.addons.decimal_precision as dp
from openerp import api, exceptions, fields, models, _
from openerp.addons.netllar_voice.models.cdr import CDR_LINE_UNIQUE_FIELDS

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


EXCEPTION_TYPES = [
    ('cli_unknown', 'Unknown CLI'),
    ('cli_unassigned', 'CLI not assigned'),
    ('prefix_not_found', 'Prefix not found')
]


class ImportException(models.Model):
    _name = "sale.telecommunications.import.exception"
    _description = "Call Detail Record (CDR) import exceptions"

    @api.multi
    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, "%s (%s)" % (record.date, record.type)))
        return result

    def _selection_line_type(self):
        return self.env['sale.telecommunications.cdr.line'].fields_get(
            allfields=['line_type']
        )['line_type']['selection']

    def _selection_line_subtype(self):
        return self.env['sale.telecommunications.cdr.line'].fields_get(
            allfields=['line_subtype']
        )['line_subtype']['selection']

    def default_line_type(self):
        return self.env['sale.telecommunications.cdr.line'].default_get(
            ['line_type']
        ).get('line_type')

    def default_line_subtype(self):
        return self.env['sale.telecommunications.cdr.line'].default_get(
            ['line_subtype']
        ).get('line_subtype')

    cdr_id = fields.Many2one(
        comodel_name='sale.telecommunications.cdr', string='CDR reference',
        required=True, readonly=True, ondelete="cascade")
    caller = fields.Char(
        string='Source number', size=30, required=True, index=True)
    caller_id = fields.Many2one(
        comodel_name='sale.telecommunications.cli', string='Source CLI',
        index=True)
    company_id = fields.Many2one(
        comodel_name="res.company", related='caller_id.company_id',
        string='Company', store=True, readonly=True,
    )
    date = fields.Datetime(
        string='Call date', required=True, index=True, readonly=True)
    dest = fields.Char(
        string='Destination number', size=30, index=True)
    dest_id = fields.Many2one(
        comodel_name='sale.telecommunications.prefix',
        string='Destination prefix')
    length = fields.Integer(
        string='Amount',
        help="Amount of the event (seconds for calls, KB for data and number "
             "for messages", required=True, readonly=True)
    prefix = fields.Char(size=30)
    line_type = fields.Selection(
        selection='_selection_line_type', string='Type', required=True,
        default=default_line_type,
    )
    line_subtype = fields.Selection(
        selection='_selection_line_subtype', string='Subtype',
        default=default_line_subtype,
    )
    type = fields.Selection(
        EXCEPTION_TYPES, 'Exception type', required=True, select=1,
        readonly=True)
    cost = fields.Float(
        string='Cost price', digits_compute=dp.get_precision('Voice price'),
        readonly=True)
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
    def _relaunch_exceptions_planned(self):
        self.search([]).relaunch_exceptions()
        return True

    @api.model
    def _send_error_mail(self, errors):
        cli_obj = self.env['sale.telecommunications.cli']
        subject = u"[Netllar ERP] Errores en la reimportación de CDRs"
        email_from = 'netllar@netllar.es'
        for company, errors in errors.iteritems():
            if not company or not company.email:
                continue
            body = (
                u"Se han producido los siguientes errores en la "
                u"reimportacion de CDRs para la compañía %s del día "
                u"%s:<br><br>\n\n" % (
                    company.name, fields.Datetime.now()))
            for cli_id, error in errors.iteritems():
                if not cli_id:
                    continue
                cli = cli_obj.browse(cli_id)
                body += u"<u>CLI nº</u>: <b>%s</b> - " % cli.name
                for exc_type in EXCEPTION_TYPES:
                    if exc_type[0] == error:
                        body += exc_type[1] + "<br>\n"
                        break
            mail_vals = {
                'email_to': company.email,
                'recipient_ids': [(6, 0, company.partner_id.ids)],
                'body_html': body,
                'email_from': email_from,
                'subject': subject,
            }
            mail = self.env['mail.mail'].create(mail_vals)
            mail.send()

    @api.multi
    def relaunch_exceptions(self):
        def batch(iterable, n=1):
            l = len(iterable)
            for ndx in range(0, l, n):
                yield iterable[ndx:min(ndx + n, l)]

        # exc_by_company = {}
        # cdr_line_obj = self.env["sale.telecommunications.cdr.line"]
        session = ConnectorSession.from_env(self.env)
        for chunk in batch(self, n=1000):
            for exception in chunk:
                reimport_exception.delay(
                    session, exception._name, exception.id)
            self.env.cr.commit()
        # self._send_error_mail(exc_by_company)
        return True


@job(default_channel='root.netllar_voice.reimport_exception')
def reimport_exception(session, model_name, exception_id):
    exception_model = session.env[model_name]
    cdr_line_obj = session.env["sale.telecommunications.cdr.line"]
    exception = exception_model.browse(exception_id)
    # This makes that the values are read and thus _cache is filled
    if not exception.exists() or not exception.type:
        return
    exception_vals = exception._convert_to_write(exception._cache)
    company = exception.cdr_id.profile_id.company_id
    del exception_vals['type']
    line_vals = cdr_line_obj._prepare_cdr_line(
        exception_vals, company_id=company.id)
    # Check if there is no error
    if line_vals.get('type'):
        # Add to a dictionary to send a message at the end
        # company_dict = exc_by_company.setdefault(company, {})
        # company_dict[line_vals['caller_id']] = line_vals['type']
        exception.write(line_vals)
    else:
        exception.unlink()
        del line_vals['caller']
        try:
            cdr_line_obj.create(line_vals)
        except Exception as e:
            _logger.error(e.message)
