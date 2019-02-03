# -*- coding: utf-8 -*-
# Copyright 2012-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2016-2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models


class Bond(models.Model):
    _name = 'sale.telecommunications.bond'

    name = fields.Char(
        'Bond name', size=100, select=1, required=True,
        help='Name of the bond.',
    )
    voice_exceeded_product_id = fields.Many2one(
        comodel_name='product.product', string='Exceeded product (voice)',
        help="Product for invoicing exceeded voice minutes of the bond.",
        ondelete='set null', required=True,
    )
    sms_exceeded_product_id = fields.Many2one(
        comodel_name='product.product', string='Exceeded product (SMS)',
        help="Product for invoicing exceeded SMS of the bond.",
        ondelete='set null', required=True,
    )
    mms_exceeded_product_id = fields.Many2one(
        comodel_name='product.product', string='Exceeded product (MMS)',
        help="Product for invoicing exceeded MMS of the bond.",
        ondelete='set null', required=True,
    )
    data_exceeded_product_id = fields.Many2one(
        comodel_name='product.product', string='Exceeded product (data)',
        help="Product for invoicing exceeded data of the bond.",
        ondelete='set null', required=True,
    )
    bond_line = fields.One2many(
        comodel_name='sale.telecommunications.bond.line',
        inverse_name='bond_id', string='Bond lines',
    )
    rule_lines = fields.One2many(
        comodel_name='sale.telecommunications.bond.rule',
        inverse_name='bond_id', string='Rule lines',
    )

    @api.multi
    def get_bond_max_allowed(self, quota):
        self.ensure_one()
        max_allowed = {}
        for bond_line in self.bond_line:
            max_type = max_allowed.setdefault(bond_line.line_type, {})
            max_subtype = max_type.setdefault(bond_line.line_subtype, {})
            if bond_line.line_type == 'call':
                max_unit = bond_line.max_minutes * 60 * quota
            elif bond_line.line_type == 'data':
                max_unit = bond_line.max_minutes * 1024 * quota
            elif bond_line.line_type in ['sms', 'mms']:
                max_unit = bond_line.max_minutes * quota
            else:
                max_unit = 0
            max_subtype.setdefault(bond_line.prefix_group_id, 0)
            max_subtype[bond_line.prefix_group_id] += max_unit
        return max_allowed


class BondLine(models.Model):
    _name = 'sale.telecommunications.bond.line'

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

    bond_id = fields.Many2one(
        comodel_name='sale.telecommunications.bond',
        string='Bond reference', ondelete='cascade', required=True,
    )
    line_type = fields.Selection(
        selection='_selection_line_type', string='Type', required=True,
        default=default_line_type, oldname='type',
    )
    line_subtype = fields.Selection(
        selection='_selection_line_subtype', string='Subtype',
        default=default_line_subtype,
    )
    max_minutes = fields.Integer(
        string='Max limit', required=True,
        help="Maximum amount of the event type (minutes for calls, "
             "number form SMS/MMS, MBs for data) available with no cost "
             "for this group of prefixes.",
    )
    prefix_group_id = fields.Many2one(
        comodel_name='sale.telecommunications.prefix_group',
        string='Prefix group', ondelete='restrict',
    )
