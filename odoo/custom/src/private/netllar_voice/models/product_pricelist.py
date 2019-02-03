# -*- coding: utf-8 -*-
# Copyright 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2017 Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import _, api, exceptions, fields, models
from openerp.addons.decimal_precision import decimal_precision as dp


class ProductPricelistVersion(models.Model):
    _inherit = 'product.pricelist.version'

    voice_line = fields.One2many(
        comodel_name='product.pricelist.voice_line', inverse_name='version_id',
        string='Voice lines',
    )
    mobile_line = fields.One2many(
        comodel_name='product.pricelist.mobile_line',
        inverse_name='version_id', string='Mobile lines',
    )
    sms_def_price = fields.Float(
        string='SMS default price', help='Default price for each SMS.',
        digits=dp.get_precision('Voice price'),
    )
    mms_def_price = fields.Float(
        strign='MMS default price', help='Default price for each MMS.',
        digits=dp.get_precision('Voice price'),
    )
    data_def_price = fields.Float(
        string='Data (MB) default price',
        digits=dp.get_precision('Voice price'),
        help='Default price for each MB data traffic.',
    )
    default_sale_rate = fields.Float(
        help="Default rate for applying to cost rate when selling items for "
             "this pricelist that doesn't have specific rate and for roaming "
             "ones.",
        default=1.25, required=True,
    )
    # TODO: Cambiar a multi-valor (category_ids)
    category = fields.Many2one(
        comodel_name='product.category', string='Product category',
    )

    @api.constrains('active', 'date_start', 'date_end')
    def _check_date(self):
        for pricelist_version in self.filtered('active'):
            # TODO: Convertir a ORM
            where = []
            if pricelist_version.date_start:
                where.append("((date_end>='%s') or (date_end is null))" % (
                    pricelist_version.date_start,))
            if pricelist_version.date_end:
                where.append("((date_start<='%s') or (date_start is null))" % (
                    pricelist_version.date_end,))
            if pricelist_version.category:
                where.append("category = %s" % pricelist_version.category.id)
            else:
                where.append("category is null")
            self.env.cr.execute(
                'SELECT id '
                'FROM product_pricelist_version '
                'WHERE ' + ' and '.join(where) + (where and ' and ' or '') +
                'pricelist_id = %s '
                'AND active '
                'AND id <> %s', (pricelist_version.pricelist_id.id,
                                 pricelist_version.id)
            )
            if self.env.cr.fetchall():
                raise exceptions.ValidationError(
                    _('You cannot have 2 pricelist versions that overlap!')
                )


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    no_bonds = fields.Boolean(
        string="No usar bonos",
        help="Marque esta casilla si no desea usar los minutos/duración "
             "máximos establecidos en el bono",
    )


class GenericVoiceLine(models.AbstractModel):
    _name = 'product.pricelist.generic_voice_line'
    _order = "version_id,prefix_id"

    def _selection_line_type(self):
        return self.env['sale.telecommunications.cdr.line'].fields_get(
            allfields=['line_type']
        )['line_type']['selection']

    def default_line_type(self):
        return self.env['sale.telecommunications.cdr.line'].default_get(
            ['line_type']
        ).get('line_type')

    prefix_id = fields.Many2one(
        comodel_name='sale.telecommunications.prefix',
        string='Prefix', ondelete='cascade',
    )
    group_id = fields.Many2one(
        comodel_name='sale.telecommunications.prefix_group',
        string='Prefix group', ondelete='cascade',
    )
    version_id = fields.Many2one(
        comodel_name='product.pricelist.version', ondelete='cascade',
        string='Pricelist version reference', required=True,
    )
    call_setup_price = fields.Float(
        string='Call setup price',
        digits_compute=dp.get_precision('Voice price'),
        help='Price of the call setup for this prefix. It can be 0.',
    )
    line_type = fields.Selection(
        selection='_selection_line_type', string='Type', required=True,
        default=default_line_type,
    )
    use_cost_price = fields.Boolean(
        string='Use cost price',
        help="Mark this field if you want to base the sale price in the "
             "cost price (with the multiplier factor introduced in the "
             "code)."
    )
    sale_rate = fields.Float(
        help="Specific sale rate to apply to the cost. If not specified, "
             "the rate applied is the general one at pricelist version level.",
    )

    @api.constrains('prefix_id', 'group_id')
    def _check_prefixes(self):
        for prefixes in self:
            if not prefixes.prefix_id and not prefixes.group_id:
                raise exceptions.ValidationError(
                    _("Either a prefix or a prefix group must be filled.")
                )


class VoiceLine(models.Model):
    _inherit = 'product.pricelist.generic_voice_line'
    _name = 'product.pricelist.voice_line'

    price = fields.Float(
        string='Minute price', digits=dp.get_precision('Voice price'),
        help='Price of a minute of voice conference for this prefix.',
        required=True,
    )

    _sql_constraints = [
        ('line_unique', 'unique(prefix_id, version_id)',
         'Voice line for prefix and version combination must be unique.'),
    ]


class MobileLine(models.Model):
    _inherit = 'product.pricelist.generic_voice_line'
    _name = 'product.pricelist.mobile_line'
    _order = "version_id,prefix_id,line_type"

    price = fields.Float(
        'Price', digits=dp.get_precision('Voice price'),
        help="Price of a unit of the concept:\n· For calls, price of a "
             "minute.\n· For SMS/MMS, price of a message.\n· For data, "
             "price of a MB.", required=True,
    )

    _sql_constraints = [
        ('line_unique', 'unique(prefix_id, version_id, line_type)',
         'Voice line for prefix, version and line type combination must '
         'be unique.'),
    ]
