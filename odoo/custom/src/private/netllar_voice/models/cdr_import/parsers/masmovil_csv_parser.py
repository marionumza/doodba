# -*- coding: utf-8 -*-
# Copyright 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime
from .csv_parser import CsvParser
from openerp import fields

CALL_TEXTS = [
    'VOZ NACIONAL',
    'NUMERO ESPECIAL',
]
SMS_TEXTS = [
    'SMS NACIONAL',
    'SMS INTERNACIONAL',
]
MMS_TEXTS = [
    'MMS NACIONAL',
]
DATA_TEXTS = [
    'DATOS NACIONAL',
    'DATOS GRATIS',
]
CALL_ROAMING_TEXTS = [
    'VOZ ROAMING',
    'VOZ RECIBIDA EN ROAMING',
    'ESPECIAL ROAMING',
]
SMS_ROAMING_TEXTS = [
    'SMS ROAMING',
]
MMS_ROAMING_TEXTS = [
    'MMS ROAMING',
]
DATA_ROAMING_TEXTS = [
    'DATOS ROAMING',
]
CALL_ROAMING_UE_TEXTS = [
    'VOZ ROAMING UE',
    'VOZ RECIBIDA EN ROAMING UE',
    'ESPECIAL ROAMING UE',
]
SMS_ROAMING_UE_TEXTS = [
    'SMS ROAMING UE',
]
MMS_ROAMING_UE_TEXTS = [
    'MMS ROAMING UE',
]
DATA_ROAMING_UE_TEXTS = [
    'DATOS ROAMING UE',
]


class MasMovilCsvParser(CsvParser):
    """Parser for CSV from MásMóvil."""
    def __init__(self, parse_name, **kwargs):
        super(MasMovilCsvParser, self).__init__(parse_name, **kwargs)

    @classmethod
    def parser_for(cls, parser_name):
        return parser_name == 'masmovil_csv'

    def get_line_vals(self, line, *args, **kwargs):
        """Maps and converts columns to the required ones."""
        val = {
            'caller': line[4],
            'date': fields.Datetime.to_string(
                datetime.strptime(line[2], '%d/%m/%Y %H:%M:%S')
            ),
            'cost': float(line[8].replace(',', '.')),
        }
        if line[5] in CALL_TEXTS:
            val['line_type'] = 'call'
            val['line_subtype'] = 'domestic'
        elif line[5] in SMS_TEXTS:
            val['line_type'] = 'sms'
            val['line_subtype'] = 'domestic'
        elif line[5] in MMS_TEXTS:
            val['line_type'] = 'mms'
            val['line_subtype'] = 'domestic'
        elif line[5] in DATA_TEXTS:
            val['line_type'] = 'data'
            val['line_subtype'] = 'domestic'
        elif line[5] in CALL_ROAMING_TEXTS:
            val['line_type'] = 'call'
            val['line_subtype'] = 'roaming'
        elif line[5] in SMS_ROAMING_TEXTS:
            val['line_type'] = 'sms'
            val['line_subtype'] = 'roaming'
        elif line[5] in MMS_ROAMING_TEXTS:
            val['line_type'] = 'mms'
            val['line_subtype'] = 'roaming'
        elif line[5] in DATA_ROAMING_TEXTS:
            val['line_type'] = 'data'
            val['line_subtype'] = 'roaming'
        elif line[5] in CALL_ROAMING_UE_TEXTS:
            val['line_type'] = 'call'
            val['line_subtype'] = 'eu'
        elif line[5] in SMS_ROAMING_UE_TEXTS:
            val['line_type'] = 'sms'
            val['line_subtype'] = 'eu'
        elif line[5] in MMS_ROAMING_UE_TEXTS:
            val['line_type'] = 'mms'
            val['line_subtype'] = 'eu'
        elif line[5] in DATA_ROAMING_UE_TEXTS:
            val['line_type'] = 'data'
            val['line_subtype'] = 'eu'
        else:
            # Nombre del país
            val['line_type'] = 'call'
            val['line_subtype'] = 'roaming'
        # Lectura de campos en función del tipo
        if val['line_type'] in ('call', 'sms', 'mms'):
            val['dest'] = line[6]
        else:
            val['dest'] = ''
        if val['line_type'] == 'data':
            val['length'] = int(line[7][:-3])  # Quitar decimales
        if val['line_type'] == 'call':
            val['length'] = int(line[7])
        if val['line_type'] in ('sms', 'mms'):
            val['length'] = 1
        return val

    def _parse(self, *args, **kwargs):
        """Launch the parsing. Override to get a CSV list reader instead a
        dict.
        """
        kwargs['csv_type'] = 'list'
        kwargs['delimiter'] = '|'
        return super(MasMovilCsvParser, self)._parse(*args, **kwargs)
