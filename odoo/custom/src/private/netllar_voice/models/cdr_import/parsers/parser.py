# -*- coding: utf-8 -*-
# (c) 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
# Adapted from Joel Grand-Guillaume work on bank_statement_base_import
# Copyright 2011-2012 Camptocamp SA

from openerp.tools.translate import _


class CdrImportParser(object):
    """
    Generic abstract class for defining parsers for different files and
    formats to import a CDR. Inherit from it to create your own.
    """

    def __init__(self, parser_name, *args, **kwargs):
        # The name of the parser as it will be called
        self.parser_name = parser_name
        # The result as a list of row. One row per line of data in the file
        self.result_row_list = None
        # The file buffer on which to work on
        self.filebuffer = None

    @classmethod
    def parser_for(cls, parser_name):
        """
        Override this method for every new parser, so that
        cdr_import_parser_factory can return the good class from his name.
        """
        return False

    def _custom_format(self, *args, **kwargs):
        """
        Implement a method in your parser to convert format, encoding and so
        on before starting to work on data. Work on self.filebuffer.
        """
        return NotImplementedError

    def _pre(self, *args, **kwargs):
        """
        Implement a method in your parser to make a pre-treatment on datas
        before parsing them, like concatenate stuff, and so... Work on
        self.filebuffer.
        """
        return NotImplementedError

    def _parse(self, *args, **kwargs):
        """
        Implement a method in your parser to save the result of parsing
        self.filebuffer in self.result_row_list instance property.
        """
        return NotImplementedError

    def _validate(self, *args, **kwargs):
        """
        Implement a method in your parser  to validate the self.result_row_list
        instance property and raise an error if not valid.
        """
        return NotImplementedError

    def _post(self, *args, **kwargs):
        """
        Implement a method in your parser to make some last changes on the
        result of parsing the data, like converting dates...
        """
        return NotImplementedError

    def get_line_vals(self, line, *args, **kwargs):
        """
        Implement a method in your parser that must return a dict of vals that
        can be passed to create method of cdr line in order to record it. It is
        the responsibility of every parser to give this dict of vals, so each
        one can implement his own way of recording the lines.
        :param:  line: a dict of vals that represent a line of result_row_list
        :return: dict of values to give to the create method of statement
          line, it MUST contain at least:
                {
                    TODO
                }
        """
        return NotImplementedError

    def parse(self, filebuffer, *args, **kwargs):
        """
        This is the method that it is called by defined methods for actions,
        buttons and so on (for instance, cdr_import of ImportProfile).
        Return:
             [] of rows as {'key':value}

        Note: The row_list must contain only values that are present in the
        cdr.line object !!!
        """
        if filebuffer:
            self.filebuffer = filebuffer
        else:
            raise Exception(_('No buffer file given.'))
        self._custom_format(*args, **kwargs)
        self._pre(*args, **kwargs)
        self._parse(*args, **kwargs)
        self._validate(*args, **kwargs)
        self._post(*args, **kwargs)
        return self.result_row_list
