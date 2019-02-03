# -*- coding: utf-8 -*-
# Copyright 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import _, api, exceptions, fields, models
from openerp.addons.decimal_precision import decimal_precision as dp
from datetime import timedelta


class Rule(models.AbstractModel):
    _name = 'sale.telecommunications.rule'
    _description = "Calculation rule"
    _order = "sequence"

    def _selection_apply_to(self):
        return self.env['sale.telecommunications.cdr.line'].fields_get(
            allfields=['line_type']
        )['line_type']['selection']

    def _selection_apply_to_subtype(self):
        return self.env['sale.telecommunications.cdr.line'].fields_get(
            allfields=['line_subtype']
        )['line_subtype']['selection']

    def _default_apply_to(self):
        return self.env['sale.telecommunications.cdr.line'].default_get(
            ['line_type']
        ).get('line_type')

    def _default_apply_to_subtype(self):
        return self.env['sale.telecommunications.cdr.line'].default_get(
            ['line_subtype']
        ).get('line_subtype')

    name = fields.Char(
        'Rule name', size=100, select=1, required=True,
        help="Name to identify the rule. This is the text that it's going "
             "to be added to the invoice line where applies.",
    )
    apply_to = fields.Selection(
        selection='_selection_apply_to',
        string='Apply to', required=True, default=_default_apply_to,
        help="Specifies to what type of consume lines this rule is going "
             "to be applied.",
    )
    apply_to_subtype = fields.Selection(
        selection='_selection_apply_to_subtype', required=True,
        default=_default_apply_to_subtype, string="Apply to subtype",
    )
    type = fields.Selection(
        selection=[
            ('base', 'Modification of the base'),
            ('price', 'Modification of the price'),
            ('no_call_setup', 'Remove call setup price'),
        ], string='Type', required=True, default="price",
        help="Specifies the calculation type for the rule.\n"
             "· Modification of the base: It modifies the base of the "
             "calculation in an amount or a percentage: the length for "
             "the calls or the quantity for data. It doesn't apply to "
             "SMS/MMS."
             "· Modification of the price: It modifies the price of the "
             "consume line in an amount or a percentage.\n"
             "· Remove call setup price: It can be applied only to "
             "calls.\n",
    )
    sequence = fields.Integer(
        string='Priority', required=True, default=10,
        help="Evaluation of the rule priority. Lower value means that the "
             "rule is evaluated first.",
    )
    disc_type = fields.Selection(
        selection=[
            ('percentage', 'Percentage'),
            ('amount', 'Amount'),
        ], string='Discount type', default="percentage",
    )
    percentage = fields.Float(
        string="Discount (%)", digits=(16, 2),
        help="Discount to be applied in percentage. You can put a "
             "negative amount for an increment.",
    )
    price = fields.Float(
        string="Discount (price)",
        digits_compute=dp.get_precision('Sale Price'),
        help="Discount in price for each consume line. You can put a "
             "negative value for an increment.",
    )
    amount = fields.Integer(
        string="Discount (amount)",
        help="Discount for each consume line in amount. You can put a "
             "negative value for an increment.",
    )

    @api.constrains('type', 'apply_to')
    def _check_no_call_setup(self):
        for rule in self.filtered(lambda x: x.type == 'no_call_setup'):
            if rule.apply_to != 'call':
                raise exceptions.Warning(
                    _("You cannot set 'No call setup' for applying to "
                      "something different than calls.")
                )

    @api.constrains('type', 'apply_to')
    def _check_base_type(self):
        for rule in self.filtered(lambda x: x.type == 'base'):
            if rule.apply_to in ('sms', 'mms'):
                raise exceptions.Warning(
                    _("You cannot set 'Modification of the base' for SMS or "
                      "MMS.")
                )

    def _getCallLength(self, rule, bond_time, length):
        """
        Get call length modified by this rule.
        @param bond_time: Remaining time of the bond before this call.
        @param length: Length of the call before this rule.
        @return: Calculated length after this rule.
        """
        if rule.disc_type == 'amount':
            discount = rule.amount
        else:
            discount = int(length * rule.percentage / 100)
        if bond_time > discount:
            return length
        else:
            res = length - (discount - bond_time)
            return res > 0 and res or 0

    def _getCallPrice(self, rule, price):
        """
        Get call price modified by this rule.
        @param price: Price of the call before this rule.
        @return: Calculated price after this rule.
        """
        if rule.disc_type == 'quantity':
            discount = rule.price
        else:
            discount = price * rule.percentage / 100
        res = price - discount
        return res > 0.0 and res or 0.0

    @api.model
    def isValid(self, rule, contract_line, date, to_date=None, dest_id=None):
        """Checks if the rule can be applied for the given date(s) and
        contract line.
        @param to_date: If set, it checks if the rule can be apply to any of
        the dates between date and to_date.
        """
        if not contract_line or not rule or not contract_line.cli_id:
            return False
        # Check if the prefix group applies
        if rule.prefix_groups and dest_id:
            for group in rule.prefix_groups:
                if group.belongsToGroup(group, dest_id):
                    return True
            return False
        return True


class BondRule(models.Model):
    _inherit = 'sale.telecommunications.rule'
    _name = 'sale.telecommunications.bond.rule'

    days_validity = fields.Integer(
        string='Days of validity',
        help="Number of days that the rule is going to be applied since "
             "the beginning of the contract. Keep empty for an unlimited "
             "validity.",
    )
    bond_id = fields.Many2one(
        comodel_name='sale.telecommunications.bond', string='Bond reference',
        ondelete='cascade', required=True,
    )
    prefix_groups = fields.Many2many(
        'sale.telecommunications.prefix_group', 'bond_rule_group_rel',
        'rule_id', 'group_id', 'Prefix groups to apply',
    )

    def isValid(self, rule, contract_line, date, to_date=None, dest_id=None):
        """Checks if the rule can be applied for the given date(s) and
        contract line.
        @param to_date: If set, it checks if the rule can be apply to any of
        the dates between date and to_date.
        """
        if not super(BondRule, self).isValid(
                rule, contract_line, date, to_date=to_date, dest_id=dest_id,
        ):
            return False
        if not rule.days_validity:
            return True
        if contract_line.start_date:
            start_date = fields.Date.from_string(contract_line.start_date)
        else:
            contract = contract_line.contract_id
            start_date = fields.Date.from_string(contract.start_date)
        days_elapsed = (date - start_date).days
        return days_elapsed < rule.days_validity


class ContractLineRule(models.Model):
    _inherit = 'sale.telecommunications.rule'
    _name = 'sale.telecommunications.contract.line.rule'

    start_date = fields.Date(
        string='Start date', index=True,
        help="Date to start applying the rule. Keep empty for no "
             "checking.",
    )
    end_date = fields.Date(
        string='End date', index=True,
        help="Date up to the rule is been applied. Keep empty for no "
             "checking.",
    )
    contract_line_id = fields.Many2one(
        comodel_name='sale.telecommunications.contract.line',
        string='Contract line reference', ondelete='cascade', required=True,
    )
    prefix_groups = fields.Many2many(
        'sale.telecommunications.prefix_group', 'contract_rule_group_rel',
        'rule_id', 'group_id', 'Prefix groups to apply',
    )

    def isValid(self, rule, contract_line, date, to_date=None, dest_id=None):
        """Checks if the rule can be applied for the given date(s) and
        contract line.
        @param to_date: If set, it checks if the rule can be apply to any of
        the dates between date and to_date.
        """
        if not super(ContractLineRule, self).isValid(
                rule, contract_line, date, to_date=to_date, dest_id=dest_id
        ):
            return False
        if not rule.start_date and not rule.end_date:
            return True
        # Make sure this var is a date, not datetime
        date = fields.Date.from_string(fields.Date.to_string(date))
        if rule.start_date:
            start_date = fields.Date.from_string(rule.start_date)
            if to_date and to_date < start_date:
                return False
            if date < start_date:
                return False
        if rule.end_date:
            end_date = fields.Date.from_string(rule.end_date)
            date += timedelta(days=1)
            if end_date > date:
                return False
        return True
