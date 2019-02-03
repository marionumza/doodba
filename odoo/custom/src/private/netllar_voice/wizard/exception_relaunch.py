# -*- coding: utf-8 -*-
# (c) 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.osv import orm


class ImportRelaunchException(orm.TransientModel):
    _name = "sale.telecommunications.import.exception.relaunch"

    def relaunch_exception(self, cr, uid, ids, context=None):
        if context.get('active_ids'):
            exception_obj = \
                self.pool["sale.telecommunications.import.exception"]
            exception_obj.relaunch_exceptions(
                cr, uid, context['active_ids'], context=context)
        return {'type': 'ir.actions.act_window_close'}
