# -*- coding: utf-8 -*-

from odoo import fields, models

class HrExpense(models.Model):
    _inherit = 'hr.expense'

    state = fields.Selection(
        selection=[
            ('draft', 'Brouillon'),
            ('reported', 'To Submit'),
            ('submitted', 'Submitted'),
            ('approved', 'Approved'),
            ('done', 'Validé'),
            ('refused', 'Refused')])
    payment_mode = fields.Selection(default='company_account')

    def action_done(self):
        self.ensure_one()
        sheets = self.env['hr.expense.sheet'].create(self._get_default_expense_sheet_values())
        sheets.action_submit_sheet()
        sheets.action_approve_expense_sheets()
        sheets.action_sheet_move_create()
