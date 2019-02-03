# -*- coding: utf-8 -*-
# (c) 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import tempfile
import csv
from .parser import CdrImportParser


def UnicodeDictReader(utf8_data, **kwargs):
    sniffer = csv.Sniffer()
    pos = utf8_data.tell()
    sample_data = utf8_data.read(2048)
    utf8_data.seek(pos)
    if 'delimiter' in kwargs:
        delimiters = kwargs['delimiter']
    else:
        delimiters = ',;\t'
    dialect = sniffer.sniff(sample_data, delimiters=delimiters)
    csv_reader = csv.DictReader(utf8_data, dialect=dialect, **kwargs)
    for row in csv_reader:
        yield dict([(key, unicode(value, 'utf-8')) for
                    key, value in row.iteritems()])


def UnicodeReader(utf8_data, **kwargs):
    sniffer = csv.Sniffer()
    pos = utf8_data.tell()
    sample_data = utf8_data.read(2048)
    utf8_data.seek(pos)
    if 'delimiter' in kwargs:
        delimiters = kwargs['delimiter']
    else:
        delimiters = ',;\t'
    dialect = sniffer.sniff(sample_data, delimiters=delimiters)
    csv_reader = csv.reader(utf8_data, dialect=dialect)
    for row in csv_reader:
        yield [unicode(value, 'utf-8') for value in row]


class CsvParser(CdrImportParser):
    """Parser for generic .csv file format."""

    def __init__(self, parse_name, **kwargs):
        """
        :param char: parse_name : The name of the parser
        """
        super(CsvParser, self).__init__(parse_name, **kwargs)

    @classmethod
    def parser_for(cls, parser_name):
        """
        Used by the cdr_import_parser_factory class factory. Return true if
        the providen name is 'csv'.
        """
        return parser_name == 'csv'

    def get_line_vals(self, line, *args, **kwargs):
        """
        Nothing to do for the moment. Mapping will occur on children classes.
        """
        return {}

    def _parse(self, *args, **kwargs):
        """
        Launch the parsing.
        """
        csv_file = tempfile.NamedTemporaryFile()
        csv_file.write(self.filebuffer)
        csv_file.flush()
        if 'csv_type' in kwargs:
            csv_type = kwargs['csv_type']
        else:
            csv_type = 'dict'
        del kwargs['csv_type']
        with open(csv_file.name, 'rU') as fobj:
            if csv_type == 'dict':
                self.result_row_list = list(UnicodeDictReader(fobj, **kwargs))
            else:
                self.result_row_list = list(UnicodeReader(fobj, **kwargs))
        return True
