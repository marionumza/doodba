# -*- coding: utf-8 -*-
# (c) 2013-2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import fields, models


class CsvImportProfile(models.Model):
    _inherit = "sale.telecommunications.import.profile"

    import_type = fields.Selection(
        selection_add=[
            ('carrier_enabler_csv', 'Carrier Enabler CSV'),
            ('asterisk_csv', 'Asterisk CSV'),
            ('airenet_voice_csv', 'AireNet CSV (voice)'),
            ('airenet_data_csv', 'AireNet CSV (data)'),
            ('airenet_sms_csv', 'AireNet CSV (SMS)'),
            ('masmovil_csv', 'MásMóvil CSV'),
        ])
