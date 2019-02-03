# -*- coding: utf-8 -*-
# (c) 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api
import base64


class CdrFileManuallyImport(models.TransientModel):
    _name = "sale.telecommunications.cdr.wizard.import_manual"

    def get_import_type_selection(self):
        profile_obj = self.env['sale.telecommunications.import.profile']
        return profile_obj._fields['import_type'].selection

    import_type = fields.Selection(
        selection="get_import_type_selection", string='Type of import',
        required=True)
    input_file = fields.Binary(string='CDR file', required=True)
    file_name = fields.Char(string='File name')
    profile_id = fields.Many2one(
        comodel_name='sale.telecommunications.import.profile',
        string='Profile',
        help='Select the profile you want to attach this manual import to.')
    # TODO: Añadir multi-compañía

    @api.onchange('profile_id')
    def onchange_profile_id(self):
        self.import_type = self.profile_id.import_type

    @api.multi
    def import_cdr(self):
        """This function invokes the import method on handler class with the
        parameters got in this wizard.
        """
        for importer in self:
            data = base64.b64decode(importer.input_file)
            importer.profile_id.cdr_import(
                importer.file_name, import_type=importer.import_type,
                data=data, manual=True)
        return True
        # TODO: Devolver la ventana con los CDRs importados
        # model_obj = self.env['ir.model.data']
        # action_obj = self.env['ir.actions.act_window']
        # action_id = model_obj.get_object_reference(
        #     'account', 'action_bank_statement_tree')[1]
        # res = action_obj.read(action_id)
        # res['domain'] = res['domain'][:-1] + ",('id', '=', %d)]" % cdr_id
        # return res
