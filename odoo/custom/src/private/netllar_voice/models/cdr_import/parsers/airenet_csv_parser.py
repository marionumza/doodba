# -*- coding: utf-8 -*-
# Copyright 2016 Serv. Tecnol. Avanzados - Pedro M. Baeza
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import datetime
from .csv_parser import CsvParser
from openerp import fields


class AireNetCsvParser(CsvParser):
    """Generic parser for CSVs from AireNet."""
    @classmethod
    def parser_for(cls, parser_name):
        return parser_name == 'airenet_csv'

    def get_line_vals(self, line, *args, **kwargs):
        """Maps and converts columns to the required ones."""
        return {
            'caller': line[2],
            'date': fields.Datetime.to_string(
                datetime.strptime(line[1], '%d/%m/%y %H:%M:%S')),
            'cost': float(line[6]),
            'length': int(line[5]),
            'dest': line[3],
        }

    def _parse(self, *args, **kwargs):
        """Launch the parsing. Override to get a CSV list reader instead a
        dict.
        """
        self.filebuffer = self.filebuffer.decode('iso-8859-1').encode('utf-8')
        kwargs['csv_type'] = 'list'
        kwargs['delimiter'] = ';'
        return super(AireNetCsvParser, self)._parse(*args, **kwargs)


class AireNetVoiceCsvParser(AireNetCsvParser):
    """Parser for voice CSVs from AireNet."""
    @classmethod
    def parser_for(cls, parser_name):
        return parser_name == 'airenet_voice_csv'

    def get_line_vals(self, line, *args, **kwargs):
        """Maps and converts columns to the required ones."""
        vals = super(AireNetVoiceCsvParser, self).get_line_vals(
            line, args, kwargs)
        vals['line_type'] = 'call'
        if 'roaming' in line[4]:
            vals['line_subtype'] = 'roaming'
        else:
            vals['line_subtype'] = 'domestic'
        return vals


class AireNetSmsCsvParser(AireNetCsvParser):
    """Parser for voice CSVs from AireNet."""
    @classmethod
    def parser_for(cls, parser_name):
        return parser_name == 'airenet_sms_csv'

    def get_line_vals(self, line, *args, **kwargs):
        """Maps and converts columns to the required ones."""
        vals = super(AireNetSmsCsvParser, self).get_line_vals(
            line, args, kwargs)
        vals['line_type'] = 'sms'
        if 'roaming' in line[4]:
            vals['line_subtype'] = 'roaming'
        else:
            vals['line_subtype'] = 'domestic'
        return vals


class AireNetDataCsvParser(AireNetCsvParser):
    """Parser for voice CSVs from AireNet."""
    @classmethod
    def parser_for(cls, parser_name):
        return parser_name == 'airenet_data_csv'

    def get_line_vals(self, line, *args, **kwargs):
        """Maps and converts columns to the required ones."""
        vals = {
            'caller': line[1],
            'date': fields.Datetime.to_string(
                datetime.strptime(line[0], '%d/%m/%y %H:%M:%S')),
            'cost': float(line[3]),
            'length': float(line[2]) / 1024.0,
            'dest': False,
            'line_type': 'data',
        }
        if 'roaming' in line[4]:
            vals['line_subtype'] = 'roaming'
        else:
            vals['line_subtype'] = 'domestic'
        return vals
