# -*- coding: utf-8 -*-
# Copyright 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, exceptions, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    group_id = fields.Many2one(
        comodel_name='res.partner', string="Grupo", oldname="group",
        domain=['|', ('is_company', '=', True), ('parent_id', '=', False)])
    mandate_ids = fields.One2many(
        comodel_name='account.banking.mandate', inverse_name='partner_id',
        string='Mandates')

    @api.multi
    def _check_company(self):
        group = self.env.ref('netllar_custom.group_edit_common_partners')
        if self.env.uid == 1 or group in self.env.user.groups_id:
            return  # Excluir usuario administrador y autorizados
        if any(not partner.company_id for partner in self):
            raise exceptions.Warning(
                'No se puede modificar o eliminar una empresa común salvo por '
                'los usuarios autorizados.')

    @api.multi
    def write(self, vals):
        self._check_company()
        return super(ResPartner, self).write(vals)

    @api.multi
    def unlink(self):
        self._check_company()
        return super(ResPartner, self).unlink()
