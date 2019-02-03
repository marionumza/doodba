# -*- coding: utf-8 -*-
# © 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# © 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Netllar voice',
    'version': '8.0.4.1.1',
    'category': 'Custom modifications',
    'author': 'Serv. Tecnol. Avanzados - Pedro M. Baeza,'
              'Tecnativa',
    'website': 'http://www.serviciosbaeza.com',
    'depends': [
        'netllar',
        'connector',
        'report_webkit',
    ],
    'license': 'AGPL-3',
    'data': [
        'data/voice_data.xml',
        'security/netllar_voice_security.xml',
        'security/ir.model.access.csv',
        'views/account_invoice_view.xml',
        'views/voice_view.xml',
        'views/cli_view.xml',
        'views/cdr_view.xml',
        'views/contract_view.xml',
        'views/bond_view.xml',
        'views/rule_view.xml',
        'views/product_pricelist_view.xml',
        'views/cdr_import/import_voice_view.xml',
        'views/cdr_import/import_voice_asterisk_http_view.xml',
        'views/cdr_import/import_voice_ftp_view.xml',
        'report/cdr_report_view.xml',
        'data/import_data.xml',
        'wizard/import_cdr_manually_view.xml',
        'wizard/exception_relaunch_view.xml',
        'report/voice_reports.xml',
    ],
    'external_dependencies': {
        'python': ['paramiko'],
    },
    'demo': [
        'demo/netllar_voice_demo.xml',
    ],
    'installable': False,
}
