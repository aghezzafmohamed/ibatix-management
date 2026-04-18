from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests


class SaasCoolify(models.Model):
    _name = 'saas.coolify'
    _description = 'Coolify Master Instance'

    name = fields.Char(string="Name", required=True, default="Coolify Main")
    api_url = fields.Char(string="API URL", required=True, help="e.g. https://app.coolify.io")
    api_token = fields.Char(string="Token (Bearer)", required=True)

    # Inverse relation to servers
    server_ids = fields.One2many('saas.server', 'coolify_id', string="Managed Servers")

    def action_ping(self):
        self.ensure_one()

        if not self.api_url or not self.api_token:
            raise UserError(_("Please configure the API URL and API Token first."))

        url = f"{self.api_url.rstrip('/')}/api/v1/servers"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Accept": "*/*",  # on accepte tout
        }

        try:
            response = requests.get(url, headers=headers, timeout=5)

            # ---- VALIDATION URL + TOKEN ----
            if response.status_code in (200, 204):
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "title": _("Success"),
                        "message": _("Coolify connection successful (URL & token valid)"),
                        "type": "success",
                    },
                }

            if response.status_code in (401, 403):
                raise UserError(_("Authentication failed: invalid or unauthorized token."))

            if response.status_code == 404:
                raise UserError(_("Invalid API URL (endpoint not found)."))

            # Autres erreurs
            raise UserError(
                _("Unexpected response from Coolify (status %s).") % response.status_code
            )

        except requests.exceptions.Timeout:
            raise UserError(_("Connection timeout. Please check the Coolify server."))

        except requests.exceptions.ConnectionError:
            raise UserError(_("Unable to reach Coolify server. Check the URL."))

        except Exception as e:
            raise UserError(_("Connection failed: %s") % str(e))

