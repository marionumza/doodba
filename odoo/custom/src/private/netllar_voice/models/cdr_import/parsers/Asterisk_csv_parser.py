# -*- coding: utf-8 -*-
# Copyright 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime
from .csv_parser import CsvParser
from openerp import fields


class AsteriskCsvParser(CsvParser):
    """Parser for CSV from Asterisk machine."""
    def __init__(self, parse_name, **kwargs):
        super(AsteriskCsvParser, self).__init__(parse_name, **kwargs)

    @classmethod
    def parser_for(cls, parser_name):
        """
        Used by the cdr_import_parser_factory class factory. Return true if
        the providen name is 'asterisk_csv'.
        """
        return parser_name == 'asterisk_csv'

    def get_line_vals(self, line, *args, **kwargs):
        """Maps and converts columns to the required ones."""
        val = {}
        if line:
            val = {
                'line_type': 'call',
                'line_subtype': 'domestic',
                'caller': line[1],
                'dest': line[2],
                'date': fields.Datetime.to_string(
                    datetime.strptime(line[3], '%Y-%m-%d %H:%M:%S')
                ),
                'length': int(line[4]),
                'cost': float(line[5].replace(',', '.')),
            }
        return val

    def _parse(self, *args, **kwargs):
        """Launch the parsing. Override to get a CSV list reader instead a
        dict.
        """
        kwargs['csv_type'] = 'list'
        kwargs['delimiter'] = ';'
        return super(AsteriskCsvParser, self)._parse(*args, **kwargs)
