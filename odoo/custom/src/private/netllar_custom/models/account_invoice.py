# -*- coding: utf-8 -*-
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, api


class AccountInvoice(models.Model):
    # Assure that the model gets the correct inheritance for applying the
    # constraint on the auto-follower subscription
    _inherit = ['mail.thread', 'account.invoice']
    _name = 'account.invoice'

    @api.multi
    def invoice_validate(self):
        res = super(AccountInvoice, self).invoice_validate()
        self.filtered(lambda x: x.type == 'out_invoice').send_invoice()
        return res

    @api.multi
    def send_invoice(self):
        for invoice in self:
            if not invoice.partner_id.email:
                return
            template = self.env.ref(
                'account.email_template_edi_invoice', False)
            ctx = dict(
                default_model='account.invoice',
                default_res_id=invoice.id,
                default_use_template=bool(template),
                default_template_id=template.id,
                default_composition_mode='mass_mail',
                mark_invoice_as_sent=True,
                lang=invoice.partner_id.lang,
            )
            obj = self.env['mail.compose.message'].with_context(ctx)
            vals = obj.onchange_template_id(
                template.id, 'mass_mail', 'account.invoice',
                invoice.id)['value']
            obj.create(vals).send_mail()
