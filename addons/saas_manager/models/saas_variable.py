from odoo import models, fields


class SaasVariable(models.Model):
    _name = 'saas.variable'
    _description = 'Coolify Environment Variable'
    _rec_name = 'key'

    env_id = fields.Many2one('saas.environment', string="Environment", required=True, ondelete='cascade')
    key = fields.Char(string="Key", required=True)
    value = fields.Char(string="Value", required=True)

    # Coolify Options
    is_preview = fields.Boolean(string="Preview", default=False, help="Active for Preview deployments (PR)")
    is_build_time = fields.Boolean(string="Build Time", default=False, help="Available during Docker build")
    is_literal = fields.Boolean(string="Literal", default=True, help="Do not escape special characters")
