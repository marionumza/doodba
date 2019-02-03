# -*- coding: utf-8 -*-
# © 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# © 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
import pytz
import base64
from pytz import timezone, utc
from datetime import datetime, timedelta
from .parsers.parser import CdrImportParser
from openerp import api, exceptions, fields, models, tools, _

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


def cdr_import_parser_factory(parser_name, *args, **kwargs):
    """Return an instance of the good parser class base on the providen name
    :param char: parser_name
    :return: class instance of parser_name providen.
    """

    def itersubclasses(cls, _seen=None):
        """itersubclasses(cls)

        Generator over all subclasses of a given class, in depth first order.

        >>> list(itersubclasses(int)) == [bool]
        True
        >>> class A(object): pass
        >>> class B(A): pass
        >>> class C(A): pass
        >>> class D(B,C): pass
        >>> class E(D): pass
        >>>
        >>> for cls in itersubclasses(A):
        ...     print(cls.__name__)
        B
        D
        E
        C
        >>> # get ALL (new-style) classes currently defined
        >>> # doctest: +ELLIPSIS
        >>> [cls.__name__ for cls in itersubclasses(object)]
        ['type', ...'tuple', ...]
        """
        if not isinstance(cls, type):
            raise TypeError('itersubclasses must be called with '
                            'new-style classes, not %.100r' % cls)
        if _seen is None:
            _seen = set()
        try:
            subs = cls.__subclasses__()
        except TypeError:  # fails only when cls is type
            subs = cls.__subclasses__(cls)
        for sub in subs:
            if sub not in _seen:
                _seen.add(sub)
                yield sub
                for sub in itersubclasses(sub, _seen):
                    yield sub

    for cls in itersubclasses(CdrImportParser):
        if cls.parser_for(parser_name):
            return cls(parser_name, *args, **kwargs)
    raise ValueError


class ImportProfile(models.Model):
    _name = "sale.telecommunications.import.profile"
    _description = "Call Detail Record (CDR) import profiles"

    def _tz_get(self, cr, uid, context=None):
        # put POSIX 'Etc/*' entries at the end to avoid confusing users -
        # see bug 1086728
        return [(tz, tz) for tz in sorted(
            pytz.all_timezones,
            key=lambda tz: tz if not tz.startswith('Etc/') else '_')]

    def _default_company_id(self):
        company_model = self.env['res.company']
        company_id = company_model._company_default_get(
            'sale.telecommunications.import.profile')
        return company_model.browse(company_id)

    name = fields.Char(
        'Name', required=True, select=1, help='Name of the importer.')
    import_type = fields.Selection(
        selection=[], string='Type of import', required=True,
        help="Choose here the format in which data are served for this "
             "profile.")
    import_source = fields.Selection(
        selection=[], string='Source of import', required=True,
        help="Choose here the source type of the data to import.")
    import_period = fields.Selection(
        selection=[('day', 'Daily'), ('month', 'Monthly')],
        string='Periodicity', required=True)
    import_day = fields.Integer(
        string='Day of month', help="Day of month for the import")
    cdr_ids = fields.One2many(
        comodel_name='sale.telecommunications.cdr', inverse_name='profile_id',
        string='CDR imports', readonly=True, copy=False)
    tz = fields.Selection(selection="_tz_get", string='Timezone', size=64)
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Supplier', required=True,
        index=True, change_default=True, domain="[('supplier', '=', True)]")
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company', required=True,
        default=_default_company_id)

    def _is_date_dependent(self, cr, uid, ids, context=None):
        return True

    @api.multi
    def _import(self, start_date=None, end_date=None):
        """ Method to override to get data from different sources."""
        return []

    @api.multi
    def _post_import(self):
        """ Method to override to make some operations after full import, like
        delete resources and so on."""
        return True

    @api.multi
    def _post_import_partial(self, name):
        """ Method to override to make some operations after an import of a
        resource, like delete this resource and so on.
        :param name: name of the resource imported.
        """
        return True

    @api.model
    def send_error_mail(self, errors, partner_id=None):
        body = (u"Se han producido los siguientes errores en la importación "
                u"de los CDRs del día %s:<br><br>\n\n" % fields.Date.today())
        for vals in errors:
            profile = vals[0]
            error = vals[1]
            if profile:
                body += u"<u>Perfil</u>: <b>%s</b> (ID: %s)<br>\n" % (
                    profile.name, profile.id)
            body += u"<u>Error</u>: %s<br><br>\n" % tools.ustr(error)
            if len(vals) > 2:
                body += u"<u>Recurso</u>: %s<br><br>\n" % vals[2]
            body += "\n"
        if not partner_id:
            partner_id = self.env.user.partner_id
        mail_vals = {
            'recipient_ids': [(6, 0, partner_id.ids)],
            'body_html': body,
            'email_from': 'netllar@netllar.es',
            'subject': u"[OpenERP] Errores en la importación de CDRs",
        }
        mail = self.env['mail.mail'].create(mail_vals)
        mail.send()

    @api.model
    def _import_planned(self):
        self.search([]).import_cdrs()
        return True

    @api.multi
    def import_cdrs(self):
        session = ConnectorSession.from_env(self.env)
        for profile in self:
            import_profile.delay(session, profile._name, profile.id)

    @api.multi
    def manual_import_cdrs(self):
        for profile in self:
            import_profile(self, profile._name, profile.id)

    @api.multi
    def cdr_import(self, name, import_type=None, data=None, manual=False):
        """Method that parses the provided file stream. Not to be overwritten
        from the children class. It is intended to be used by an action button
        or similar.
        """
        self.ensure_one()
        session = ConnectorSession.from_env(self.env)
        _logger.info("Importing '%s'" % name)
        cdr_obj = self.env["sale.telecommunications.cdr"]
        cdr_line_obj = self.env["sale.telecommunications.cdr.line"]
        exception_obj = self.env["sale.telecommunications.import.exception"]
        attachment_obj = self.env["ir.attachment"]
        if not import_type and manual:
            raise exceptions.Warning(
                _("You must provide a valid type to import a CDR file"))
        parser = cdr_import_parser_factory(import_type)
        # Don't import again if exists
        if cdr_obj.search([('profile_id', '=', self.id), ('name', '=', name)]):
            return _('CDR already exists.')
        # Create main record
        cdr_vals = {
            'name': name,
            'import_type': import_type,
            'date': fields.Datetime.now(),
            'profile_id': self.id,
        }
        result_row_list = []
        if data:
            cdr = cdr_obj.create(cdr_vals)
            result_row_list = parser.parse(data)
        if not data or not result_row_list:
            msg = _("No data has been fetched (due to an error or no events).")
            if manual:
                raise exceptions.Warning(msg)
            else:
                return msg
        # Process every line
        for cdr_line in result_row_list:
            parser_vals = parser.get_line_vals(cdr_line)
            if not parser_vals:
                continue  # Discard empty lines
            parser_vals['cdr_id'] = cdr.id
            # Process timezone
            if self.tz:
                date = fields.Datetime.from_string(parser_vals['date'])
                local_tz = timezone(self.tz)
                date = local_tz.localize(date)
                date = date.astimezone(utc)
                parser_vals['date'] = fields.Datetime.to_string(date)
            if manual:
                line_vals = cdr_line_obj._prepare_cdr_line(
                    parser_vals, company_id=self.company_id.id)
                if (line_vals.get('type') and
                        not cdr_line_obj._is_duplicated(line_vals)):
                    exception_obj.create(line_vals)
                else:
                    del line_vals['caller']
                    if 'type' in line_vals:
                        del line_vals['type']
                    cdr_line_obj.create(line_vals)
            else:
                import_cdr_line.delay(
                    session, self._name, self.id, parser_vals)
        if data:
            # Save the attachment
            attachment_vals = {
                'name': name,
                'datas': base64.encodestring(data),
                'datas_fname': name,
                'res_model': 'sale.telecommunications.cdr',
                'res_id': cdr.id,
            }
            attachment_obj.create(attachment_vals)
            _logger.info("CDR with ID %s has been created with %s lines." %
                         (cdr.id, len(result_row_list)))
        return


@job(default_channel='root.netllar_voice.import_cdr')
def import_profile(session, model_name, profile_id):
    profile_model = session.env[model_name]
    profile = profile_model.browse(profile_id)
    if not profile.exists():
        return _(u'Nothing to do because the record has been deleted')
    _logger.info("Importing CDRs from '%s'" % profile.name)
    datas = {}
    now = datetime.now()
    if profile._is_date_dependent():
        # Get last imported file date
        last_date = fields.Date.from_string(
            max(profile.mapped('cdr_ids.date') or [False])
        )
        if profile.import_period == 'day':
            if not last_date:
                last_date = (now - timedelta(days=1)).date()
            while last_date < now.date():
                # Asterisk take the same end date as the starting one
                end_date = last_date
                datas.update(profile._import(
                    start_date=last_date, end_date=end_date))
                last_date += timedelta(days=1)
        elif profile.import_period == 'month':
            # TODO: Implementar
            raise NotImplementedError('Opción no válida')
    else:
        datas = profile._import()
    for name, data in datas.iteritems():
        profile.cdr_import(
            name, import_type=profile.import_type, data=data, manual=False)
        profile._post_import_partial(name)
    profile._post_import()


@job(default_channel='root.netllar_voice.import_cdr')
def import_cdr_line(session, model_name, profile_id, parser_vals):
    profile_model = session.env[model_name]
    profile = profile_model.browse(profile_id)
    cdr_line_obj = session.env["sale.telecommunications.cdr.line"]
    cdr_line_obj = cdr_line_obj.with_context(no_constraint=True)
    exception_obj = session.env["sale.telecommunications.import.exception"]
    exception_obj = exception_obj.with_context(no_constraint=True)
    line_vals = cdr_line_obj._prepare_cdr_line(
        parser_vals, company_id=profile.company_id.id)
    # It's needed to pre-check the duplicity because the ValidationError on the
    # constraint closes the cursor and hangs the connector queue
    if line_vals.get('type'):
        if not exception_obj._is_duplicated(line_vals):
            exception_obj.create(line_vals)
    else:
        if not cdr_line_obj._is_duplicated(line_vals):
            del line_vals['caller']
            cdr_line_obj.create(line_vals)
