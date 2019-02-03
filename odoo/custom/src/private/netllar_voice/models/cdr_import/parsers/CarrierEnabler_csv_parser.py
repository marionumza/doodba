# -*- coding: utf-8 -*-
# Copyright 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import datetime
from .csv_parser import CsvParser
from openerp import fields


class CarrierEnablerCsvParser(CsvParser):
    """Parser for CSV from Carrier Enabler."""

    def __init__(self, parse_name, **kwargs):
        super(CarrierEnablerCsvParser, self).__init__(parse_name, **kwargs)

    @classmethod
    def parser_for(cls, parser_name):
        """
        Used by the cdr_import_parser_factory class factory. Return true if
        the providen name is 'carrier_enabler_csv'.
        """
        return parser_name == 'carrier_enabler_csv'

    def get_line_vals(self, line, *args, **kwargs):
        """Maps and converts columns to the required ones."""
        val = {}
        if line:
            val = {
                'line_type': 'call',
                'line_subtype': 'domestic',
                'caller': line['Caller_ID'],
                'dest': line['Called_Number'],
                'date': fields.Datetime.to_string(datetime.datetime.strptime(
                    line['Call_Start'], '%Y-%m-%d %H:%M:%S',
                )),
                'length': int(line['Duration(s)']),
                'cost': float(line['Cost']),
                'prefix': line['Tariff_Prefix'],
                'comment': line['Tariffdesc'],
            }
        return val

    def _parse(self, *args, **kwargs):
        """
        Remove final ';'.
        """
        self.filebuffer = self.filebuffer.replace(';\r\n', '\r\n')
        return super(CarrierEnablerCsvParser, self)._parse(*args, **kwargs)
