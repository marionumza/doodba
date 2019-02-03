# -*- coding: utf-8 -*-
# (c) 2013-2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import models, fields, api
from ftplib import FTP
import fnmatch
import os.path
import paramiko


class FtpImportProfile(models.Model):
    _inherit = "sale.telecommunications.import.profile"

    import_source = fields.Selection(
        selection_add=[('ftp', 'FTP/SFTP')])

    def _is_date_dependent(self, cr, uid, ids, context=None):
        profile = self.browse(cr, uid, ids[0], context=context)
        if profile.import_source == 'ftp':
            return False
        else:
            return super(FtpImportProfile, self)._is_date_dependent(
                cr, uid, ids, context=context)

    def _import(self, start_date=None, end_date=None):
        self.ensure_one()
        if self.import_source == 'ftp':
            if self.ftp_sftp:
                return self._import_sftp()
            else:
                self.files = []
                return self._import_ftp()
        else:
            return super(FtpImportProfile, self)._import(
                start_date=start_date, end_date=end_date)

    @api.multi
    def _post_import(self):
        self.ensure_one()
        if self.import_source == 'ftp':
            if self.ftp_sftp:
                return self._post_import_sftp()
            else:
                return self._post_import_ftp()
        else:
            return super(FtpImportProfile, self)._post_import()

    @api.multi
    def _post_import_partial(self, name):
        self.ensure_one()
        if self.import_source == 'ftp':
            if self.ftp_sftp:
                return self._post_import_partial_sftp(name)
            else:
                # return self._post_import_partial_ftp(profile, name)
                return True
        else:
            return super(FtpImportProfile, self)._post_import_partial(name)

    @api.multi
    def _import_ftp(self):
        self.ensure_one()
        self.ftp = FTP(self.ftp_host)
        if self.ftp_user:
            self.ftp.login(user=self.ftp_user, passwd=self.ftp_password)
        else:
            self.ftp.login()
        if self.ftp_path:
            self.ftp.cwd(self.ftp_path)
        self.files = self.ftp.dir(callback=self._add_file)
        if self.ftp_files:
            self.files = fnmatch.filter(self.files, self.ftp_files)
        datas = {}
        for ftp_file in self.files:
            data = self.ftp.retrbinary('RETR %s' % ftp_file)
            datas[file] = data
        return datas

    @api.multi
    def _import_sftp(self):
        self.ensure_one()
        self.transport = paramiko.Transport((self.ftp_host, self.ftp_port))
        if self.ftp_user:
            self.transport.connect(
                username=self.ftp_user, password=self.ftp_password)
        self.sftp = paramiko.SFTPClient.from_transport(self.transport)
        self.files = self.sftp.listdir(path=self.ftp_path or '/')
        if self.ftp_files:
            self.files = fnmatch.filter(self.files, self.ftp_files)
        # Filter already imported files
        self.files = filter(lambda x: '_IMPORTED' not in x, self.files)
        datas = {}
        for ftp_file in self.files:
            if self.ftp_path:
                f = self.sftp.open(
                    os.path.join(self.ftp_path, ftp_file), 'rb')
            else:
                f = self.sftp.open(ftp_file, 'rb')
            data = f.read()
            datas[ftp_file] = data
        return datas

    @api.multi
    def _post_import_ftp(self):
        self.ensure_one()
        self.ftp.close()
        return True

    @api.multi
    def _post_import_sftp(self):
        self.ensure_one()
        self.sftp.close()
        self.transport.close()
        return True

    def rexists(self, path, filename):
        """os.path.exists for paramiko's SFTP object"""
        files = self.sftp.listdir(path)
        return filename in files

    @api.multi
    def _post_import_partial_sftp(self, name):
        self.ensure_one()
        path = self.ftp_path or '/'
        path_before = os.path.join(path, name)
        path_after = os.path.join(path, name + "_IMPORTED")
        # First remove possible existing files with this name
        if self.rexists(path, name + "_IMPORTED"):
            self.sftp.remove(path_after)
        try:
            self.sftp.rename(path_before, path_after)
        except:
            # For possible permission denied problems
            pass
        return True

    ftp_sftp = fields.Boolean('SFTP?')
    ftp_host = fields.Char(
        'Host', size=100, help="IP or domain name of the host of the FTP")
    ftp_port = fields.Integer('Port', default=21)
    ftp_user = fields.Char(
        'User', size=100,
        help="User to login in the FTP server. If not set, the connection "
             "will be anonymous.")
    ftp_password = fields.Char('Password', size=100)
    ftp_path = fields.Char(
        'Path', size=256,
        help="Path of the FTP server where getting files. If not set, "
             "path will be /.")
    ftp_files = fields.Char(
        string='File pattern', size=100,
        help="File pattern of the files to import. Use wildcards (*) to "
             "match any substring. Leave empty for importing any found "
             "file.")
