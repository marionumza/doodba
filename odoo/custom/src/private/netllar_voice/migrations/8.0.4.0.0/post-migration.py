# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openupgradelib import openupgrade

SUBTYPE_MAPPING = [
    ('call_roaming', 'roaming'),
    ('sms_roaming', 'roaming'),
    ('mms_roaming', 'roaming'),
    ('data_roaming', 'roaming'),
]

TYPE_MAPPING = [
    ('call_roaming', 'call'),
    ('sms_roaming', 'sms'),
    ('mms_roaming', 'mms'),
    ('data_roaming', 'data'),
]


def map_value_same_table(cr, column, mapping, table):
    """Variation from standard openupgradelib for mapping values (not boolean)
    because it doesn't allow to map the same column."""
    for old, new in mapping:
        values = {
            'table': table,
            'source': column,
            'target': column,
            'old': old,
            'new': new,
        }
        query = """UPDATE %(table)s
                   SET %(target)s = '%(new)s'
                   WHERE %(source)s = '%(old)s'""" % values
        openupgrade.logged_query(cr, query, values)


@openupgrade.migrate()
def migrate(cr, version):
    # These columns hasn't been renamed as the creation with the default value
    # takes too much time and invalid values are not checked anyway on module
    # upgrade, so we fix here the possible values and everything is OK
    openupgrade.map_values(
        cr, 'line_type', 'line_subtype',
        SUBTYPE_MAPPING, table='sale_telecommunications_cdr_line',
    )
    map_value_same_table(
        cr, 'line_type',
        TYPE_MAPPING, 'sale_telecommunications_cdr_line',
    )
    openupgrade.map_values(
        cr, 'line_type', 'line_subtype',
        SUBTYPE_MAPPING, table='sale_telecommunications_bond_line',
    )
    map_value_same_table(
        cr, 'line_type',
        TYPE_MAPPING, 'sale_telecommunications_bond_line',
    )
    openupgrade.map_values(
        cr, 'line_type', 'line_subtype',
        SUBTYPE_MAPPING, table='sale_telecommunications_import_exception',
    )
    map_value_same_table(
        cr, 'line_type',
        TYPE_MAPPING, 'sale_telecommunications_import_exception',
    )
