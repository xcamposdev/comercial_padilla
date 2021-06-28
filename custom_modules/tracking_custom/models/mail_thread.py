# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class MailThread_Tracking_Custom(models.AbstractModel):

    _inherit = 'mail.thread'

    @api.model
    def _get_tracked_fields(self):
        super(MailThread_Tracking_Custom, self)._get_tracked_fields()
        tracked_fields = []
        if self._name == 'res.partner' or self._name == 'product.product' or self._name == 'product.template':
            for name, field in self._fields.items():
                if name not in ['write_date', '__last_update'] and not getattr(field, 'readonly', None):
                    tracked_fields.append(name)
        else:
            for name, field in self._fields.items():
                tracking = getattr(field, 'tracking', None) or getattr(field, 'track_visibility', None)
                if tracking:
                    tracked_fields.append(name)

        if tracked_fields:
            return self.fields_get(tracked_fields)
        return {}