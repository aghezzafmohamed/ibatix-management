# -*- coding: utf-8 -*-

from odoo import models, api


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _message_log_batch(self, bodies, subject=False, author_id=None, email_from=None, message_type='notification', partner_ids=False, attachment_ids=False, tracking_value_ids=False):
        if self._context.get('create_emp'):
            return True
        return super()._message_log_batch( bodies, subject, author_id, email_from, message_type, partner_ids, attachment_ids, tracking_value_ids)
