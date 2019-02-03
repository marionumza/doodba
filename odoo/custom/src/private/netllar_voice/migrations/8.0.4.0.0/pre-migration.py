# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openupgradelib import openupgrade

BATCH_SIZE = 10000


@openupgrade.migrate()
def migrate(cr, version):
    # Pre-create column and assign default value by chunks for avoiding Odoo to
    # do it, as Odoo performs it in one block and saturates the system
    cr.execute(
        "ALTER TABLE sale_telecommunications_cdr_line ADD line_subtype VARCHAR"
    )
    cr.execute(
        """
        SELECT COUNT(*) FROM sale_telecommunications_cdr_line
        WHERE line_subtype IS NULL
        """
    )
    count = cr.fetchone()[0]
    index = 0
    while index < count:
        cr.execute(
            """
            UPDATE sale_telecommunications_cdr_line
            SET line_subtype = 'domestic'
            WHERE id IN (
                SELECT id FROM sale_telecommunications_cdr_line
                WHERE line_subtype IS NULL
                LIMIT %s
            )
            """ % BATCH_SIZE
        )
        index += BATCH_SIZE
