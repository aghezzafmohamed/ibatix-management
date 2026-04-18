from odoo import models, fields, _

class Project(models.Model):
    _inherit = 'project.project'

    saas_instance_count = fields.Integer(compute='_compute_saas_count')

    def _compute_saas_count(self):
        for project in self:
            project.saas_instance_count = self.env['saas.instance'].search_count([('project_id', '=', project.id)])

    def action_view_saas_instances(self):
        self.ensure_one()
        return {
            'name': _('Instances SaaS'),
            'type': 'ir.actions.act_window',
            'res_model': 'saas.instance',
            'view_mode': 'list,form',
            'domain': [('project_id', '=', self.id)],
            'context': {'default_project_id': self.id}
        }