# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TaskTest(models.Model):
    _name = "task.test"
    _description = 'Task Test'

    name = fields.Text('Description')
    sequence = fields.Integer(string='Sequence')
    tested = fields.Boolean(string="Tested")
    date = fields.Datetime(string="Tested Date")
    task_id = fields.Many2one('project.task', ondelete='cascade')

    @api.onchange('tested')
    def _compute_tasks_count(self):
        for rec in self:
            if rec.tested:
                rec.date = fields.Datetime.now()
            else:
                rec.date = False
