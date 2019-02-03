# -*- coding: utf-8 -*-
# © 2015 Oihane Crucelaegui - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, fields, models, tools
from openerp.addons import decimal_precision as dp


class SaleTelecommunicationsCdrLineReport(models.Model):
    _name = "sale.telecommunications.cdr.line.report"
    _description = "Call Detail Record (CDR) line Report"
    _auto = False

    @api.model
    def _get_line_type_selection(self):
        return self.env["sale.telecommunications.cdr.line"].fields_get(
            allfields=["line_type"])["line_type"]["selection"]

    @api.model
    def _get_import_type_selection(self):
        return self.env["sale.telecommunications.cdr"].fields_get(
            allfields=["import_type"])["import_type"]["selection"]

    cdr_name = fields.Char(string="CDR name")
    company_id = fields.Many2one(comodel_name="res.company", string="Company")
    caller_id = fields.Many2one(
        comodel_name="sale.telecommunications.cli", string="Source CLI")
    line_type = fields.Selection(
        selection="_get_line_type_selection", string="Type")
    profile_id = fields.Many2one(
        comodel_name="sale.telecommunications.import.profile",
        string="Profile")
    import_type = fields.Selection(
        selection="_get_import_type_selection", string="Type of import")
    invoice_id = fields.Many2one(
        comodel_name="account.invoice", string="Invoice reference")
    date = fields.Datetime(string="Call date")
    dest = fields.Char(string="Destination number")
    dest_id = fields.Many2one(
        comodel_name="sale.telecommunications.prefix",
        string="Destination prefix")
    length = fields.Integer(string="Amount", group_operator="sum")
    prefix = fields.Char(string="Prefix")
    price = fields.Float(
        string="Sale price", digits=dp.get_precision('Voice price'))
    cost = fields.Float(
        string="Cost price", digits=dp.get_precision('Voice price'))
    comment = fields.Char(string="Additional comments")
    import_date = fields.Datetime(string="Import date")

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
              SELECT MIN(id) AS id,
                cdr_name,
                invoice_id,
                company_id,
                caller_id,
                line_type,
                import_type,
                AVG(price) AS price,
                AVG(cost) AS cost,
                profile_id,
                import_date,
                date,
                SUM(length) AS length,
                dest,
                dest_id
                FROM ((
                  SELECT line.id AS id,
                    cdr.name AS cdr_name,
                    line.invoice_id AS invoice_id,
                    line.company_id AS company_id,
                    line.caller_id AS caller_id,
                    line.line_type AS line_type,
                    cdr.import_type AS import_type,
                    cdr.profile_id AS profile_id,
                    line.price AS price,
                    line.cost AS cost,
                    cdr.date AS import_date,
                    line.date AS date,
                    line.length AS length,
                    line.dest AS dest,
                    line.dest_id AS dest_id
                  FROM
                    sale_telecommunications_cdr_line AS line
                  LEFT JOIN
                    sale_telecommunications_cdr AS cdr ON line.cdr_id = cdr.id
                )) AS cdr_line
                GROUP BY
                  invoice_id, company_id, caller_id, line_type, import_type,
                  profile_id, cdr_name, import_date, date, dest, dest_id
            )""" % self._table)
