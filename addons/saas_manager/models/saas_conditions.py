from odoo import models, fields


class SaasLicenseConditionUser(models.Model):
    _name = 'saas.license.condition.user'
    _description = 'User Limit per Group'

    type_id = fields.Many2one('saas.license.type', string="License Type", ondelete='cascade')

    group_xml_id = fields.Char(
        string="Group XML ID",
        required=True,
        default='base.group_user',
        help="e.g. sales_team.group_sale_manager"
    )
    max_users = fields.Integer(string="Authorized Limit", default=5, required=True)


class SaasLicenseConditionModule(models.Model):
    _name = 'saas.license.condition.module'
    _description = 'Module Restriction'

    type_id = fields.Many2one('saas.license.type', string="License Type", ondelete='cascade')

    module_technical_name = fields.Char(
        string="Module Technical Name",
        required=True,
        help="e.g. account_accountant"
    )

    behavior = fields.Selection([
        ('forbidden', 'Forbidden (Must not be installed)'),
        ('mandatory', 'Mandatory (Must be installed)'),
    ], string="Rule", default='forbidden', required=True)