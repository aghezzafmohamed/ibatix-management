from odoo import models, fields


class SaasLicenseType(models.Model):
    _name = 'saas.license.type'
    _description = 'License Type / Plan'

    name = fields.Char("Plan Name", required=True, placeholder="e.g. Enterprise Starter")
    product_id = fields.Many2one('product.product', string="Linked Odoo Product", help="For invoicing")
    duration_months = fields.Integer(string="Default Duration (Months)", default=12, required=True)
    user_condition_ids = fields.One2many('saas.license.condition.user', 'type_id', string="User Quotas")
    module_condition_ids = fields.One2many('saas.license.condition.module', 'type_id', string="Module Rules")
    docker_compose_template = fields.Text(
            string="Template Docker Compose",
            default="""version: '3.8'
    services:
      odoo:
        image: odoo:17.0
        environment:
          - HOST=${DOMAIN_URL}
          - USER=odoo
          - PASSWORD=${DB_PASSWORD}
        volumes:
          - odoo-web-data:/var/lib/odoo
          - ./config:/etc/odoo
        restart: always
      db:
        image: postgres:15
        environment:
          - POSTGRES_DB=postgres
          - POSTGRES_PASSWORD=${DB_PASSWORD}
          - POSTGRES_USER=odoo
        volumes:
          - odoo-db-data:/var/lib/postgresql/data
        restart: always
    volumes:
      odoo-web-data:
      odoo-db-data:
    """
        )