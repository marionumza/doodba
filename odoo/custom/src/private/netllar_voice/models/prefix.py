# -*- coding: utf-8 -*-
# (c) 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.osv import orm, fields


class Prefix(orm.Model):

    def __get_length(self, cr, uid, ids, field_name, arg, context=None):
        """Get prefix length."""
        if not ids:
            return {}
        res = {}
        for prefix in self.browse(cr, uid, ids, context=context):
            res[prefix.id] = len(prefix.name)
        return res

    _name = 'sale.telecommunications.prefix'
    _order = "prefix,name"
    _columns = {
        'name': fields.char('Prefix name', size=100, select=1, required=True,
                            help='Name to identify the prefix.'),
        'prefix': fields.char('Prefix', size=15, select=1, required=True,
                              help='Sequence of digits that forms the '
                              'prefix. It can be of any length.'),
        'country_id': fields.many2one('res.country', 'Country',
                                      select=1, required=True),
        'type': fields.selection(
            [('land', 'Land line'),
             ('mobile', 'Mobile'),
             ('special', 'Special number')],
            'Type', required=True, help="Sets the type of the prefix."),
        'length': fields.function(__get_length, string='Prefix length',
                                  type='integer', method=True),
    }

    def name_get(self, cursor, uid, ids, context=None):
        # TODO: Ordenar por prefijo
        res = []
        for prefix in self.browse(cursor, uid, ids, context=context):
            res.append((prefix.id, "%s (%s)" % (prefix.name, prefix.prefix)))
        return res

    def name_search(self, cr, uid, name, args=None, operator='ilike',
                    context=None, limit=100):
        if name:
            ids = self.search(cr, uid, [('name', operator, name)] + args,
                              limit=limit)
            if not ids:
                ids = self.search(cr, uid, [('prefix', operator, name)] + args,
                                  limit=limit)
            return self.name_get(cr, uid, ids, context=context)
        else:
            return super(Prefix, self).name_search(
                cr, uid, name, args=args, operator=operator, context=context,
                limit=limit)

    def get_full_prefix(self, cr, uid, p_id, context=None):
        prefix = self.browse(cr, uid, p_id, context=context)
        return "00%s" % prefix.name

    def get_short_prefix(self, cr, uid, p_id, context=None):
        prefix = self.browse(cr, uid, p_id, context=context)
        return "+%s" % prefix.name

    def belongs(self, cr, uid, p_id, cli_number, context=None):
        prefix = self.browse(cr, uid, p_id, context=context)
        if cli_number.startswith('+'):
            cli_number = cli_number[1:]
        if cli_number.startswith('00'):
            cli_number = cli_number[2:]
        return cli_number.startswith(prefix.name)


class PrefixGroup(orm.Model):
    _name = 'sale.telecommunications.prefix_group'
    _columns = {
        'name': fields.char(
            'Prefix group name', size=50, select=1, required=True,
            help='Name of the group of prefixes.'),
        'prefix_line': fields.many2many(
            'sale.telecommunications.prefix', 'group_prefix_rel', 'group_id',
            'prefix_id', 'Prefix lines'),
    }

    # TODO: Convert this to new API style with @api.multi and self.ensure_one
    def belongsTo(self, cr, uid, ids, prefix_id, context=None):
        for group in self.browse(cr, uid, ids, context=context):
            if self.belongsToGroup(cr, uid, group, prefix_id, context=context):
                return True
        return False

    def belongsToGroup(self, cr, uid, group, prefix_id, context=None):
        for prefix_line in group.prefix_line:
            if prefix_id == prefix_line.id:
                return True
        return False
