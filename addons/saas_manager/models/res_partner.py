from odoo import models, fields, api, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # String in English
    instance_count = fields.Integer(compute='_compute_instance_count', string="Instance Count")

    def _compute_instance_count(self):
        # Optimization: fetch data in a single SQL query via read_group
        Instance = self.env['saas.instance']

        # Note: Ensure 'saas.instance' is the correct model name (previously saas.cluster?)
        data = Instance.read_group(
            [('partner_id', 'in', self.ids)],
            ['partner_id'],
            ['partner_id']
        )

        # Create a dictionary {partner_id: count}
        mapped_data = {
            item['partner_id'][0]: item['partner_id_count']
            for item in data if item['partner_id']
        }

        for partner in self:
            partner.instance_count = mapped_data.get(partner.id, 0)

    def action_view_instances(self):
        """ Opens the list view of instances for this client """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            # Translatable string in English
            'name': _('SaaS Projects / Instances'),
            'res_model': 'saas.instance',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }