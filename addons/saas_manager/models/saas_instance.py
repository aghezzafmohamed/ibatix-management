from odoo import models, fields, api, _
from odoo.exceptions import UserError
import paramiko
import io
import logging
import requests
_logger = logging.getLogger(__name__)


class SaasInstance(models.Model):
    _name = 'saas.instance'
    _description = 'Client Project (Instance)'

    name = fields.Char(string="Instance Name", required=True)

    # --- BUSINESS INFO ---
    partner_id = fields.Many2one('res.partner', string="Customer", required=True)
    project_id = fields.Many2one('project.project', string="Linked Odoo Project")

    # --- LICENSES ---
    license_ids = fields.One2many('saas.license', 'instance_id', string="Licenses")

    # Helper to see if client has a valid active license
    has_valid_license = fields.Boolean(compute='_compute_license_status', string="Active License")
    coolify_uuid = fields.Char(string="UUID Projet Coolify", readonly=True,
                               help="L'identifiant unique du Projet dans Coolify")
    # Link project to physical server
    server_id = fields.Many2one('saas.server', string="Hosting Server", required=True)

    # Convenient fields to see info without clicking
    coolify_id = fields.Many2one(related='server_id.coolify_id', string="Via Coolify", store=True)

    environment_ids = fields.One2many('saas.environment', 'instance_id', string="Environments")

    status_overview = fields.Selection([
        ('ok', 'Operational'),
        ('warning', 'Warning'),
        ('down', 'Critical')
    ], compute='_compute_status', string="Global Status")

    env_count = fields.Integer(compute='_compute_counts', string="Env Count")
    license_count = fields.Integer(compute='_compute_counts', string="License Count")

    def _get_coolify_api(self):
        """ Helper pour récupérer URL/Token depuis le serveur assigné """
        self.ensure_one()
        coolify = self.server_id.coolify_id
        if not coolify:
            raise UserError(_("Aucun master Coolify configuré sur le serveur associé."))
        return coolify.api_url.rstrip('/'), coolify.api_token

    def action_create_coolify_project(self):
        """ Crée le Projet dans Coolify si ce n'est pas déjà fait """
        self.ensure_one()
        if self.coolify_uuid:
            return self.coolify_uuid  # Déjà existant

        base_url, token = self._get_coolify_api()
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        # Payload pour créer un projet
        payload = {
            "name": f"{self.partner_id.name} - {self.name}",
            "description": f"Instance Odoo gérée par Odoo SaaS Manager"
        }

        try:
            # Endpoint Coolify v4 pour créer un projet
            url = f"{base_url}/api/v1/projects"
            res = requests.post(url, json=payload, headers=headers, timeout=10)

            if res.status_code in [200, 201]:
                data = res.json()
                # On récupère l'UUID retourné
                uuid = data.get('uuid')
                self.coolify_uuid = uuid

                self.message_post(body=_("✅ Projet Coolify créé avec succès. UUID : %s") % uuid)
                return uuid
            else:
                error_msg = res.text
                _logger.error(f"Coolify Project Error: {error_msg}")
                raise UserError(_("Impossible de créer le projet Coolify (%s) : %s") % (res.status_code, error_msg))

        except Exception as e:
            raise UserError(_("Erreur de connexion API : %s") % str(e))

    @api.depends('license_ids.state')
    def _compute_license_status(self):
        for instance in self:
            instance.has_valid_license = any(l.state == 'valid' for l in instance.license_ids)

    @api.depends('environment_ids', 'license_ids')
    def _compute_counts(self):
        for record in self:
            record.env_count = len(record.environment_ids)
            record.license_count = len(record.license_ids)

    # --- SMART BUTTONS ACTIONS ---
    def action_view_environments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Environments'),
            'res_model': 'saas.environment',
            'view_mode': 'list,form',
            'domain': [('instance_id', '=', self.id)],
            'context': {'default_instance_id': self.id},
        }

    def action_view_licenses(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Licenses'),
            'res_model': 'saas.license',
            'view_mode': 'list,form',
            'domain': [('instance_id', '=', self.id)],
            'context': {'default_instance_id': self.id},
        }

    def _get_pkey_object(self):
        """
        Robust utility method to load the SSH key.
        """
        self.ensure_one()
        if not self.server_id.ssh_key:
            raise UserError(_("Missing SSH Key."))

        # 1. Cleanup
        key_content = self.server_id.ssh_key.strip()
        key_stream = io.StringIO(key_content)

        # 2. List of key types to test
        key_types = []

        if hasattr(paramiko, 'RSAKey'):
            key_types.append(paramiko.RSAKey)
        if hasattr(paramiko, 'Ed25519Key'):
            key_types.append(paramiko.Ed25519Key)
        if hasattr(paramiko, 'ECDSAKey'):
            key_types.append(paramiko.ECDSAKey)

        last_error = None

        # 3. Loading attempts
        for k_cls in key_types:
            try:
                key_stream.seek(0)
                pkey = k_cls.from_private_key(key_stream)
                return pkey
            except (paramiko.SSHException, ValueError) as e:
                last_error = e
                pass

        _logger.error(f"SSH Key loading error: {str(last_error)}")
        raise UserError(_(
            "Unsupported key format or invalid key.\n"
            "Last error: {}\n\n"
            "Tip: Use a standard RSA or Ed25519 key (OpenSSH format)."
        ).format(str(last_error)))

    def action_test_ssh(self):
        """ Test connection and retrieve current user """
        self.ensure_one()

        try:
            pkey = self._get_pkey_object()

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            _logger.info(f"Test SSH to {self.server_id.ssh_ip}...")

            client.connect(
                hostname=self.server_id.ssh_ip,
                port=self.server_id.ssh_port,
                username=self.server_id.ssh_user,
                pkey=pkey,
                timeout=5,
                banner_timeout=5
            )

            stdin, stdout, stderr = client.exec_command('whoami')
            user_result = stdout.read().decode().strip()
            client.close()

            if not user_result:
                raise UserError(_("Connection established but no response from command 'whoami'."))

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success!'),
                    'message': _("SSH connection operational.\nServer: {}\nUser detected: {}").format(
                        self.server_id.ssh_ip, user_result
                    ),
                    'type': 'success',
                    'sticky': False,
                }
            }

        except UserError as e:
            raise e
        except Exception as e:
            _logger.exception("SSH Connection Failed")
            raise UserError(_("Connection failed: {}").format(str(e)))

    @api.depends('environment_ids.state')
    def _compute_status(self):
        for instance in self:
            states = instance.environment_ids.mapped('state')
            if not states:
                instance.status_overview = 'ok'
            elif any(s in ['exited', 'failed'] for s in states):
                instance.status_overview = 'down'
            elif any(s == 'stopped' for s in states):
                instance.status_overview = 'warning'
            else:
                instance.status_overview = 'ok'

    def action_refresh_all_statuses(self):
        """ Button to refresh status of all environments """
        for env in self.environment_ids:
            # Check previously validated file saas_environment.py for this method name
            if hasattr(env, 'action_refresh_all'):
                env.action_refresh_all()

    def action_create_coolify_project(self):
        """ ÉTAPE 1 : Créer le Projet dans Coolify """
        self.ensure_one()
        if self.coolify_uuid:
            return self.coolify_uuid

        base_url, token = self._get_coolify_api()
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        # API Coolify : POST /projects
        payload = {
            "name": f"{self.partner_id.name} - {self.name}",
            "description": f"Instance Odoo pour {self.partner_id.name}"
        }

        try:
            # Note: Adaptez l'endpoint selon votre version API Coolify v4
            res = requests.post(f"{base_url}/api/v1/projects", json=payload, headers=headers, timeout=10)

            if res.status_code in [200, 201]:
                data = res.json()
                # L'UUID est souvent retourné directement ou dans 'uuid'
                uuid = data.get('uuid')
                self.coolify_uuid = uuid

                # Log chatter
                self.message_post(body=_("Projet Coolify créé avec succès : %s") % uuid)
                return uuid
            else:
                raise UserError(_("Erreur création Projet Coolify (%s) : %s") % (res.status_code, res.text))
        except Exception as e:
            raise UserError(_("Erreur connexion Coolify : %s") % str(e))