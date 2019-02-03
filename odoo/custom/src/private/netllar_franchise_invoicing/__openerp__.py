# -*- coding: utf-8 -*-
# (c) 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Netllar - Facturación a franquicias',
    'version': '8.0.2.1.0',
    'category': 'Custom modifications',
    'author': 'Serv. Tecnol. Avanzados - Pedro M. Baeza,'
              'Tecnativa',
    'website': 'https://www.tecnativa.com',
    'depends': [
        'account',
        'netllar_voice',
    ],
    'data': [
        'wizard/invoice_franchises_view.xml',
        'views/account_invoice_view.xml',
        'report/franchise_invoicing_report.xml',
        'security/ir.model.access.csv',
    ],
    'installable': False,
}
