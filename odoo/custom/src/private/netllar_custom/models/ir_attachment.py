# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################
from openerp.osv import orm


class IrAttachment(orm.Model):
    _inherit = 'ir.attachment'

    def create(self, cr, uid, vals, context=None):
        """Remove always company_id value"""
        new_id = super(IrAttachment, self).create(
            cr, uid, vals, context=context)
        self.write(cr, uid, new_id, {'company_id': False}, context=context)
        return new_id
