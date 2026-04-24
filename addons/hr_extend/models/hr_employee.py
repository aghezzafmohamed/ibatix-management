# -*- coding: utf-8 -*-

from odoo import models, api


class Employee(models.Model):
    _inherit = 'hr.employee'

    @api.model_create_multi
    def create(self, vals_list):
        self = self.with_context(create_emp=True)
        res = super(Employee, self).create(vals_list)
        self.with_context(create_emp=False)
        return res
