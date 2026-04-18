from odoo import models, fields, api, _
from odoo.exceptions import UserError
import paramiko
import io
import logging

_logger = logging.getLogger(__name__)


class SaasServer(models.Model):
    _name = 'saas.server'
    _description = 'Physical Server / Worker'

    name = fields.Char(string="Server Name", required=True, placeholder="e.g. Worker-01 (Hetzner)")
    coolify_uuid = fields.Char(string="UUID Serveur (Coolify)", required=True, help="L'ID du serveur dans l'interface Coolify")
    # Link to the master controlling this server
    coolify_id = fields.Many2one('saas.coolify', string="Coolify Instance (Master)", required=True)

    # Projects hosted on this server
    instance_ids = fields.One2many('saas.instance', 'server_id', string="Client Projects")

    # --- SSH CONFIGURATION (Moved here) ---
    ssh_ip = fields.Char(string="Public IP", required=True)
    ssh_port = fields.Integer(string="SSH Port", default=22)
    ssh_user = fields.Char(string="User", default="root")
    ssh_key = fields.Text(string="SSH Private Key", help="For Docker logs")

    def _get_pkey_object(self):
        """ Shared method to load the key """
        self.ensure_one()
        if not self.ssh_key:
            raise UserError(_("SSH Key missing on Server record."))

        key_content = self.ssh_key.strip()
        key_stream = io.StringIO(key_content)
        key_types = [paramiko.RSAKey, paramiko.Ed25519Key, paramiko.ECDSAKey]

        last_error = None
        for k_cls in key_types:
            try:
                key_stream.seek(0)
                return k_cls.from_private_key(key_stream)
            except Exception as e:
                last_error = e
                pass

        raise UserError(_("Invalid key. Error: {}").format(str(last_error)))

    def action_test_ssh(self):
        """ Test SSH connection """
        self.ensure_one()
        try:
            pkey = self._get_pkey_object()
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            client.connect(self.ssh_ip, port=self.ssh_port, username=self.ssh_user, pkey=pkey, timeout=5)
            client.exec_command('whoami')
            client.close()

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _("SSH Connection OK on {}").format(self.ssh_ip),
                    'type': 'success'
                }
            }
        except Exception as e:
            raise UserError(_("SSH Error: {}").format(str(e)))