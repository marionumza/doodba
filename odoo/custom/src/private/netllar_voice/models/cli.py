# -*- coding: utf-8 -*-
# Copyright 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp.osv import orm, fields

cli_types = {
    '5': 'land',
    '6': 'mobile',
    '7': 'mobile',
    '8': 'land',
    '9': 'land',
}


class Cli(orm.Model):
    _name = 'sale.telecommunications.cli'

    def _get_assigned(self, cr, uid, ids, name, arg, context=None):
        result = {}
        for cli in self.browse(cr, uid, ids, context=context):
            result[cli.id] = bool(cli.contract_line_id)
        return result

    def _get_contract_line(self, cr, uid, ids, name, arg, context=None):
        result = {}
        contract_line_obj = self.pool['sale.telecommunications.contract.line']
        contract_line_ids = contract_line_obj.search(cr, uid, [],
                                                     context=context)
        contract_lines = contract_line_obj.read(cr, uid, contract_line_ids,
                                                ['cli_id'], context=context)
        for cli_id in ids:
            result[cli_id] = False
        for contract_line in contract_lines:
            if contract_line['cli_id'] and contract_line['cli_id'][0] in ids:
                result[contract_line['cli_id'][0]] = contract_line['id']
        return result

    def _get_clis_affected(self, cr, uid, ids, context=None):
        result = []
        line_obj = self.pool['sale.telecommunications.contract.line']
        for line in line_obj.browse(cr, uid, ids, context=context):
            # TODO: Tener en cuenta si se ha vaciado el campo
            if line.cli_id:
                result.append(line.cli_id.id)
        return result

    def get_cli_type_selection(self, cr, uid, context=None):
        """This is the method to be inherited for adding types"""
        return [('land', 'Land'),
                ('mobile', 'Mobile')]

    def _get_cli_type_selection(self, cr, uid, context=None):
        return self.get_cli_type_selection(cr, uid, context=context)

    _columns = {
        'active': fields.boolean('Active'),
        'name': fields.char(
            'CLI number', size=15, select=1, required=True,
            help='Number associated to a CLI.'),
        'assigned': fields.function(
            _get_assigned, string="Is assigned?", type='boolean',
            store={
                'sale.telecommunications.contract.line': (
                    _get_clis_affected, ['cli_id'], 20)}),
        'contract_line_id': fields.function(
            _get_contract_line,
            string="Contract line associated", type='many2one',
            relation='sale.telecommunications.contract.line',
            store={
                'sale.telecommunications.contract.line': (
                    _get_clis_affected, ['cli_id'], 20),
                'sale.telecommunications.cli': (
                    lambda self, cr, uid, ids, context=None: ids,
                    ['contract_line_id'], 20)
            }, ondelete="set null"),
        'type': fields.selection(
            _get_cli_type_selection, 'Type of CLI', required=True),
        'company_id': fields.many2one('res.company', 'Company', select=1),
    }

    _sql_contrains = {
        ('unique_name', 'unique(name)', 'You cannot put a duplicate CLI.'),
    }

    _defaults = {
        'active': True,
        'type': 'land',
        'company_id': lambda self, cr, uid, context=None: (
            self.pool['res.company']._company_default_get(
                cr, uid, 'sale.telecommunications.cli', context=context)),
    }

    def _get_type_from_cli(self, cli):
        if len(cli) == 9:
            for cli_type in cli_types:
                if cli.startswith(cli_type):
                    return cli_types[cli_type]
        else:
            return 'land'

    def create(self, cr, uid, vals=None, context=None):
        if vals is None:
            vals = {}
        if not vals.get('type'):
            cli_type = self._get_type_from_cli(vals.get('name'))
            if not cli_type:
                raise orm.except_orm(
                    'Valor no válido', 'El prefijo del número no es válido.')
            vals['type'] = cli_type
        return super(Cli, self).create(cr, uid, vals, context)

    def view_contract(self, cr, uid, ids, context=None):
        """Method for viewing contract associated to a CLI."""
        cli = self.browse(cr, uid, ids[0], context=context)
        if cli.contract_line_id:
            contract_id = cli.contract_line_id.contract_id.id
            # Get view to show
            data_obj = self.pool['ir.model.data']
            result = data_obj._get_id(
                cr, uid, 'netllar',
                'view_sale_telecommunications_contract_form')
            view_id = data_obj.browse(cr, uid, result).res_id
            # Return view with invoice created
            return {
                'domain': "[('id','=', " + str(contract_id) + ")]",
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'sale.telecommunications.contract',
                'context': context,
                'res_id': contract_id,
                'view_id': [view_id],
                'type': 'ir.actions.act_window',
                'nodestroy': True
            }
        else:
            return True

    def onchange_name(self, cr, uid, ids, name=False, context=None):
        if name:
            cli_type = self._get_type_from_cli(name)
            if cli_type:
                return {'value': {'type': cli_type}}
            return {
                'value': {'name': ''},
                'warning': {'title': 'Valor no válido',
                            'message': 'El prefijo del número no es válido.'}
            }
