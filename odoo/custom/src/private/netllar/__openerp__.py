# -*- coding: utf-8 -*-
# Copyright 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Netllar',
    'version': '9.0.1.1.0',
    'category': 'Custom modifications',
    'license': 'AGPL-3',
    'author': 'Serv. Tecnol. Avanzados - Pedro M. Baeza,'
              'Tecnativa',
    'website': 'https://www.tecnativa.com',
    'depends': [
        'account',
        'account_invoice_pricelist',
        'connector',
        'sale',
        'l10n_es_account_invoice_sequence',
    ],
    'data': [
        'security/netllar_security.xml',
        'security/ir.model.access.csv',
        'data/contract_data.xml',
        'views/contract_view.xml',
        'views/account_invoice_view.xml',
        'views/account_journal_view.xml',
    ],
    'installable': False,
}
