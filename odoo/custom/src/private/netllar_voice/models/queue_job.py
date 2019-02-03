# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from openerp import api, models


class QueueJob(models.Model):
    _inherit = 'queue.job'

    @api.cr_uid_ids_context
    def message_post(
            self, cr, uid, thread_id, body='', subject=None,
            type='notification', subtype=None, parent_id=False,
            attachments=None, context=None, content_subtype='html', **kwargs):
        return False
