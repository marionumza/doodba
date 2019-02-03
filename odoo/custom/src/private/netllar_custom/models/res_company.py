# -*- coding: utf-8 -*-
from openerp.osv import orm, fields


class ResCompany(orm.Model):
    _inherit = "res.company"

    _columns = {
        'rapport_ratio': fields.float('Rapport ratio'),
        'rapport_minimum': fields.float('Rapport minimum'),
    }
