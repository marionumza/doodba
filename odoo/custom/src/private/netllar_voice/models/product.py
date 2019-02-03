# -*- coding: utf-8 -*-
# (c) 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields


class ProductProduct(models.Model):
    _inherit = 'product.product'

    bond_id = fields.Many2one(
        comodel_name='sale.telecommunications.bond',
        string='Associated bond',
        help='Defines if there is a bond associated to this product. If set, '
             'contract lines with this product will need a CLI.')
