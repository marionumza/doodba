# -*- coding: utf-8 -*-
# (c) 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import fields, models


class ManualImportProfile(models.Model):
    _inherit = "sale.telecommunications.import.profile"

    import_source = fields.Selection(
        selection_add=[('manual', 'Manual')])
