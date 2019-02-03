# -*- encoding: utf-8 -*-
##############################################################################
# Copyright (c) 2015: Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
# License AGPL-3. See manifest file for full information
##############################################################################
from openerp import models, fields


class Contract(models.Model):
    _inherit = 'sale.telecommunications.contract'

    user_id = fields.Many2one(
        comodel_name='res.users', related='partner_id.user_id',
        string='Salesman', store=True)
