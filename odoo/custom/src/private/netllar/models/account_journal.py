# -*- coding: utf-8 -*-
# Copyright 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    anticipation_days = fields.Integer(
        string='Anticipation days', default=4,
        help='Sets the days that contracts associated to this journal are '
             'going to anticipate invoicing day. If set to 0, no '
             'anticipation is done.',
    )
