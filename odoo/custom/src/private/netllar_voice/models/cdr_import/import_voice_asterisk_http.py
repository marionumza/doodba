# -*- coding: utf-8 -*-
# (c) 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api
from datetime import datetime, timedelta
from openerp.exceptions import Warning as UserError
try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen


class HttpImportProfile(models.Model):
    _inherit = "sale.telecommunications.import.profile"

    import_source = fields.Selection(
        selection_add=[('asterisk_http', 'Asterisk HTTP')])
    initial_date = fields.Date()

    @api.multi
    def _import(self, start_date=None, end_date=None):
        self.ensure_one()
        if self.import_source == 'asterisk_http':
            return self._import_asterisk_http(start_date, end_date)
        else:
            return super(HttpImportProfile, self)._import(
                start_date=start_date, end_date=end_date)

    @api.multi
    def _import_asterisk_http(self, start_date, end_date):
        self.ensure_one()
        start = start_date.strftime('%Y-%m-%d')
        end = end_date.strftime('%Y-%m-%d')
        url = "http://%s/listado/index.php?desde=%s&hasta=%s" % (
            self.asterisk_host, start, end)
        try:
            response = urlopen(url, timeout=10)
            return {'%s-%s' % (start, end): response.read()}
        except:
            return []

    asterisk_host = fields.Char(
        'Host', size=100,
        help="IP or domain name of the host where Asterisk PBX is "
             "accesible. It mustn't include URI scheme (http://) or path "
             "(/listado/index.php)")

    @api.multi
    def initial_import_asterisk_http(self):
        """Method for initial import of an Asterisk HTTP PBX."""
        for profile in self:
            if self.initial_date:
                start_date = fields.Date.from_string(self.initial_date)
            else:
                # A date very old
                start_date = datetime(year=2000, month=1, day=1)
            end_date = datetime.now() - timedelta(days=1)
            datas = profile._import(
                start_date=start_date, end_date=end_date)
            if not datas:
                raise UserError(
                    'No hay datos que importar aún. Inténtelo más tarde.')
            for name, data in datas.iteritems():
                profile.cdr_import(
                    name, import_type=profile.import_type, data=data,
                    manual=True)
