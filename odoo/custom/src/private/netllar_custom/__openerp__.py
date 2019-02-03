# -*- coding: utf-8 -*-
# © 2012-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# © 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Netllar custom',
    'version': '8.0.1.3.3',
    'category': 'Custom modifications',
    'author': 'Serv. Tecnol. Avanzados - Pedro M. Baeza',
    'website': 'http://www.serviciosbaeza.com',
    'depends': [
        'base',
        'netllar',
        'mail_restrict_auto_follower',
        'account_payment',
        'account_payment_return',
        'crm_claim',
        'crm_claim_code',
        'account_banking_sepa_direct_debit',
    ],
    'data': [
        'data/netllar_custom_data.xml',
        'security/netllar_security.xml',
        'views/res_partner_view.xml',
        'views/res_partner_bank_view.xml',
        'views/crm_claim_view.xml',
        'views/account_invoice_view.xml',
        'wizard/payment_order_create_view.xml',
    ],
    'installable': False,
}
