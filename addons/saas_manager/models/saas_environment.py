from odoo import models, fields, api, _
from odoo.exceptions import UserError
import requests
import logging
import base64
import paramiko
import hashlib
import time

_logger = logging.getLogger(__name__)


class SaasEnvironment(models.Model):
    _name = 'saas.environment'
    _description = 'Technical Environment (Coolify)'
    _inherit = ['mail.thread']

    # --- GENERAL FIELDS ---
    name = fields.Char(compute='_compute_name', store=True)
    instance_id = fields.Many2one('saas.instance', string="Parent Instance", required=True, ondelete='cascade')
    env_type = fields.Selection([
        ('production', 'Prod'),
        ('staging', 'Staging'),
        ('dev', 'Dev')
    ], default='production', string="Environment Type")

    coolify_uuid = fields.Char(string="Global Service UUID", required=True)
    coolify_env_uuid = fields.Char(string="Env UUID")
    domain_url = fields.Char(string="Public URL")

    # --- CALCULATED GLOBAL STATUS ---
    state = fields.Selection([
        ('running', 'Running'),
        ('starting', 'Starting...'),
        ('stopped', 'Stopped'),
        ('exited', 'Crashed / Error'),
        ('restarting', 'Restarting...'),
        ('warning', 'Unstable / Mixed'),
        ('unknown', 'Unknown')
    ], string="Global Status", compute='_compute_global_state', store=True, tracking=True)

    last_log = fields.Html(string="Latest Logs", readonly=True)

    # --- ODOO SECTION ---
    odoo_uuid = fields.Char(string="Odoo UUID", readonly=True)
    odoo_image = fields.Char(string="Odoo Image", readonly=True)
    odoo_status = fields.Selection([
        ('running', 'Running'), ('stopped', 'Stopped'),
        ('exited', 'Exited'), ('starting', 'Starting'),
        ('restarting', 'Restarting'), ('unknown', 'Unknown')
    ], string="Odoo Status", default='unknown')
    odoo_logs = fields.Html(string="Odoo Logs", readonly=True)

    # --- GITHUB CONFIG ---
    github_url = fields.Char(string="GitHub Repo URL", placeholder="https://github.com/org/repo.git")
    github_branch = fields.Char(string="Branch", default="main")
    github_token = fields.Char(string="GitHub Token (PAT)", groups="base.group_system")

    # --- ODOO CONFIG ---
    odoo_master_password = fields.Char(string="Odoo Master Password", groups="base.group_system")

    # --- POSTGRES SECTION ---
    postgres_uuid = fields.Char(string="DB UUID", readonly=True)
    postgres_image = fields.Char(string="Postgres Image", readonly=True)
    postgres_status = fields.Selection([
        ('running', 'Running'), ('stopped', 'Stopped'),
        ('exited', 'Exited'), ('starting', 'Starting'),
        ('restarting', 'Restarting'), ('unknown', 'Unknown')
    ], string="Postgres Status", default='unknown')
    postgres_logs = fields.Html(string="Postgres Logs", readonly=True)

    variable_ids = fields.One2many('saas.variable', 'env_id', string="Env Variables")
    docker_compose = fields.Text(string="Docker Compose Content (Raw)")
    audit_token = fields.Char(
        string="Token Agent (Secret)",
        help="Clé secrète partagée avec l'agent client pour le SSO et l'audit",
        groups="base.group_system"  # Sécurité : seul l'admin doit voir ça
    )

    # --- GLOBAL STATUS LOGIC ---
    @api.depends('odoo_status', 'postgres_status')
    def _compute_global_state(self):
        for rec in self:
            o = rec.odoo_status
            p = rec.postgres_status

            # 1. Perfect Cases
            if o == 'running' and p == 'running':
                rec.state = 'running'
            elif o == 'stopped' and p == 'stopped':
                rec.state = 'stopped'

            # 2. Transient Cases
            elif o in ('starting', 'restarting') or p in ('starting', 'restarting'):
                rec.state = 'starting' if 'starting' in (o, p) else 'restarting'

            # 3. Error Cases
            elif o == 'exited' or p == 'exited':
                rec.state = 'exited'

            # 4. Mixed Cases
            elif o != 'unknown' and p != 'unknown' and o != p:
                rec.state = 'warning'

            # 5. Default
            else:
                rec.state = 'unknown'

    @api.depends('instance_id.name', 'env_type')
    def _compute_name(self):
        for record in self:
            suffix = "prod" if record.env_type == 'production' else "test"
            record.name = f"{record.instance_id.name}-{suffix}" if record.instance_id else _("New")

    # --- API HELPERS ---
    def _get_api_config(self):
        self.ensure_one()
        coolify = self.instance_id.server_id.coolify_id

        if not coolify or not coolify.api_url:
            raise UserError(_("Coolify configuration not found via assigned server."))

        return coolify.api_url.rstrip('/'), coolify.api_token

    def _coolify_request(self, method, endpoint, payload=None):
        base_url, token = self._get_api_config()
        endpoint = endpoint.lstrip('/').replace('api/v1/', '')
        full_url = f"{base_url}/api/v1/{endpoint}"
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        try:
            res = requests.request(method, full_url, headers=headers, json=payload, timeout=20)

            if not res.ok:
                error_body = res.text
                _logger.error(f"Coolify API Error ({res.status_code}) : {error_body}")
                raise UserError(_("Coolify refused the request ({}):\n{}").format(res.status_code, error_body))

            return res.json()

        except requests.exceptions.RequestException as e:
            _logger.error(f"API Connection Error: {e}")
            raise UserError(_("Coolify connection error: {}").format(str(e)))

    def _parse_status(self, raw_status):
        st = (raw_status or '').lower()
        if 'running' in st: return 'running'
        if 'stop' in st: return 'stopped'
        if 'exit' in st or 'fail' in st: return 'exited'
        if 'restart' in st: return 'restarting'
        return 'unknown'

    def _format_logs(self, raw_logs):
        """ Formats logs for HTML display with robust parsing """
        if not raw_logs:
            return _("<i>No logs available (Empty response).</i>")

        content = ""

        if isinstance(raw_logs, list):
            lines = []
            for entry in raw_logs[-100:]:
                if isinstance(entry, dict):
                    line_text = entry.get('line', '') or entry.get('message', '') or str(entry)
                else:
                    line_text = str(entry)
                line_text = line_text.replace('<', '&lt;').replace('>', '&gt;')
                lines.append(line_text)
            content = "<br/>".join(lines)

        elif isinstance(raw_logs, dict):
            if 'logs' in raw_logs and isinstance(raw_logs['logs'], list):
                return self._format_logs(raw_logs['logs'])
            content = str(raw_logs).replace('\n', '<br/>')

        else:
            content = str(raw_logs).replace('\n', '<br/>')

        return f"<div style='background: black; color: #00ff00; padding: 10px; font-family: monospace; height: 350px; overflow-y: scroll; font-size: 11px; white-space: pre-wrap;'>{content}</div>"

    def action_refresh_all(self):
        self.ensure_one()
        if not self.coolify_uuid: return

        # 1. Global Service Info
        data = self._coolify_request('GET', f"services/{self.coolify_uuid}")
        if not data:
            self.state = 'unknown'
            return

        # --- DOCKER COMPOSE FETCH ---
        self.docker_compose = data.get('docker_compose_raw') or data.get('docker_compose')

        # 2. Parsing Odoo
        apps = data.get('applications', [])
        odoo_app = next(
            (a for a in apps if 'odoo' in (a.get('name') or '').lower() or 'odoo' in (a.get('image') or '').lower()),
            None)

        if not odoo_app and apps:
            odoo_app = next((a for a in apps if 'postgres' not in (a.get('name') or '').lower()), apps[0])

        if odoo_app:
            self.odoo_uuid = odoo_app.get('uuid')
            self.odoo_image = odoo_app.get('image')
            self.odoo_status = self._parse_status(odoo_app.get('status'))
        else:
            self.odoo_status = 'unknown'
            self.odoo_logs = _("Odoo application not found in this service.")

        # 3. Parsing Postgres
        dbs = data.get('databases', [])
        pg_db = next((d for d in dbs if 'postgres' in (d.get('name') or '').lower()), None)
        if not pg_db and dbs: pg_db = dbs[0]

        if pg_db:
            self.postgres_uuid = pg_db.get('uuid')
            self.postgres_image = pg_db.get('image')
            self.postgres_status = self._parse_status(pg_db.get('status'))
        else:
            self.postgres_status = 'unknown'
            self.postgres_logs = _("Database not found.")

        # SSH Logs
        if self.odoo_status != 'unknown':
            _logger.info("Fetching Odoo logs via SSH...")
            ssh_logs = self._get_logs_via_ssh('odoo')
            self.odoo_logs = self._format_logs(ssh_logs)

        if self.postgres_status != 'unknown':
            ssh_logs = self._get_logs_via_ssh('postgres')
            self.postgres_logs = self._format_logs(ssh_logs)

    def _get_logs_via_ssh(self, container_name_part):
        self.ensure_one()
        server = self.instance_id.server_id

        if not server or not server.ssh_ip:
            return _("Server not configured for this instance.")

        try:
            pkey = server._get_pkey_object()

            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            client.connect(
                hostname=server.ssh_ip,
                port=server.ssh_port,
                username=server.ssh_user,
                pkey=pkey,
                timeout=10
            )

            uuid_clean = self.coolify_uuid.strip()
            cmd_list = f"docker ps -a --format '{{{{.Names}}}}' | grep '{uuid_clean}'"

            stdin, stdout, stderr = client.exec_command(cmd_list)
            candidates_raw = stdout.read().decode('utf-8').strip()

            if not candidates_raw:
                client.close()
                return _("❌ No container found on server matching UUID '{}'.").format(uuid_clean)

            candidates = [c.strip() for c in candidates_raw.split('\n') if c.strip()]
            real_name = next((name for name in candidates if container_name_part in name), None)

            if not real_name:
                client.close()
                return _(
                    "⚠️ Container '{}' not found.\nHowever, found these containers linked to UUID:\n{}\nCheck the keyword.").format(
                    container_name_part, ' | '.join(candidates))

            cmd_logs = f"docker logs --tail 200 {real_name} 2>&1"
            stdin, stdout, stderr = client.exec_command(cmd_logs)
            logs = stdout.read().decode('utf-8', errors='replace')

            client.close()

            if not logs:
                return _("✅ Container '{}' found, but logs are empty.").format(real_name)

            return logs

        except Exception as e:
            return _("🔥 SSH Technical Error: {}").format(str(e))

    # --- ACTION BUTTONS ---
    def action_start(self):
        self.ensure_one()
        self._coolify_request('POST', f"services/{self.coolify_uuid}/start")
        self.odoo_status = 'starting'
        self.postgres_status = 'starting'

    def action_stop(self):
        self.ensure_one()
        self._coolify_request('POST', f"services/{self.coolify_uuid}/stop")
        self.odoo_status = 'stopped'
        self.postgres_status = 'stopped'

    def action_restart(self):
        self.ensure_one()
        self._coolify_request('POST', f"services/{self.coolify_uuid}/restart")
        self.odoo_status = 'restarting'
        self.postgres_status = 'restarting'

    def action_fetch_logs(self):
        """ Fetch info and generate Coolify Logs link """
        self.ensure_one()
        if not self.coolify_uuid: return

        data = self._coolify_request('GET', f"services/{self.coolify_uuid}")
        is_service = True

        if not data:
            data = self._coolify_request('GET', f"applications/{self.coolify_uuid}")
            is_service = False

        if data:
            base_url, _ = self._get_api_config()
            proj = data.get('project_uuid') or (data.get('project') or {}).get('uuid') or data.get('projectUuid')
            env = data.get('environment_uuid') or (data.get('environment') or {}).get('uuid') or data.get(
                'environmentUuid')

            if proj and env:
                resource_type = "service" if is_service else "application"
                link = f"{base_url}/project/{proj}/environment/{env}/{resource_type}/{self.coolify_uuid}"
                status_color = "#4caf50" if 'running' in data.get('status', '').lower() else "#f44336"

                # Note: Keeping HTML structure, translating text content
                msg = _("""
                <div style="background-color: #1e1e1e; color: #d4d4d4; padding: 20px; border-radius: 8px; font-family: monospace;">
                    <div style="margin-bottom: 15px;">
                        <span style="color: #888;">UUID:</span> {uuid}<br/>
                        <span style="color: #888;">Type:</span> {type}<br/>
                        <span style="color: #888;">State:</span> <span style="color: {color}; font-weight: bold;">{status}</span>
                    </div>

                    <div style="padding: 10px; background: #2d2d2d; border-left: 4px solid #f48fb1; margin-bottom: 20px;">
                        <p style="margin: 0; color: #f48fb1;"><strong>Note:</strong> For a Docker Compose Service, logs are multiple (one per container). Please use the Coolify console.</p>
                    </div>

                    <a href="{link}" target="_blank" style="display: inline-block; background-color: #6366f1; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: bold;">
                        <i class="fa fa-external-link"></i> Open Coolify Console
                    </a>
                </div>
                """).format(
                    uuid=self.coolify_uuid,
                    type=resource_type.upper(),
                    color=status_color,
                    status=data.get('status', 'UNKNOWN').upper(),
                    link=link
                )
                self.last_log = msg
            else:
                keys_found = ", ".join(data.keys())
                import json
                json_preview = json.dumps(data, indent=2, default=str)[:500]

                self.last_log = _("""
                [METADATA ERROR]
                Cannot find 'project_uuid' or 'environment_uuid'.

                --- DEBUG ---
                Found keys: {}

                JSON Preview:
                {}
                """).format(keys_found, json_preview)
        else:
            self.last_log = _(
                "[FATAL ERROR] Cannot fetch data for UUID {}. Check if it is a Service or Application and if Token has read rights.").format(
                self.coolify_uuid)

    def action_fetch_vars(self):
        """ Fetch variables from Coolify (GET) """
        self.ensure_one()
        if not self.coolify_uuid: return

        data = self._coolify_request('GET', f"services/{self.coolify_uuid}/envs")

        if isinstance(data, list):
            self.variable_ids.unlink()

            new_vars = []
            for item in data:
                new_vars.append({
                    'env_id': self.id,
                    'key': item.get('key'),
                    'value': item.get('value'),
                    'is_preview': item.get('is_preview', False),
                    'is_build_time': item.get('is_buildtime', False),
                    'is_literal': item.get('is_literal', True),
                })

            self.env['saas.variable'].create(new_vars)

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('{} variables fetched.').format(len(new_vars)),
                    'type': 'success',
                    'sticky': False,
                }
            }

    def action_push_vars(self):
        """ Push Odoo variables to Coolify (PATCH Bulk) """
        self.ensure_one()
        if not self.coolify_uuid: return

        payload_data = []
        for var in self.variable_ids:
            payload_data.append({
                "key": var.key,
                "value": var.value,
                "is_preview": var.is_preview,
                "is_buildtime": var.is_build_time,
                "is_literal": var.is_literal
            })

        if not payload_data:
            return

        try:
            self._coolify_request('PATCH', f"services/{self.coolify_uuid}/envs/bulk", payload={"data": payload_data})
            message = _("Variables updated (Bulk Mode).")
        except Exception:
            count = 0
            for item in payload_data:
                self._coolify_request('PATCH', f"services/{self.coolify_uuid}/envs", payload=item)
                count += 1
            message = _("{} variables updated (Iterative Mode).").format(count)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Coolify Update'),
                'message': _("{} Don't forget to RESTART the service to apply!").format(message),
                'type': 'warning',
                'sticky': True,
            }
        }

    def action_save_compose(self):
        self.ensure_one()
        if not self.coolify_uuid: return

        if not self.docker_compose:
            raise UserError(_("Docker Compose content cannot be empty."))

        try:
            ascii_content = self.docker_compose.encode('ascii', errors='ignore').decode('ascii')
            encoded_bytes = base64.b64encode(ascii_content.encode('ascii'))
            encoded_string = encoded_bytes.decode('ascii')

        except Exception as e:
            raise UserError(_("Error cleaning file: {}").format(str(e)))

        payload = {
            "docker_compose_raw": encoded_string
        }

        try:
            self._coolify_request('PATCH', f"services/{self.coolify_uuid}", payload=payload)
            self._coolify_request('POST', f"deploy?uuid={self.coolify_uuid}")

            self.odoo_status = 'restarting'
            self.postgres_status = 'restarting'

            msg = _("Configuration saved and deployment started!")
            if len(ascii_content) != len(self.docker_compose):
                msg += _("\n(Note: Special characters unsupported by Coolify were automatically removed)")

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': msg,
                    'type': 'success',
                    'sticky': False,
                }
            }
        except UserError as e:
            raise e
        except Exception as e:
            raise UserError(_("Technical Error: {}").format(str(e)))

    def action_provision_full_stack(self):
        """
        MÉTHODE MAGIQUE :
        1. Vérifie/Crée le Projet
        2. Vérifie/Crée l'Environnement
        3. Crée le Service (Docker Compose)
        """
        self.ensure_one()

        # --- ETAPE 1 : LE PROJET ---
        # On vérifie si l'instance parente a déjà un UUID projet
        if not self.instance_id.coolify_uuid:
            _logger.info("Projet Coolify manquant, création en cours...")
            self.instance_id.action_create_coolify_project()

        project_uuid = self.instance_id.coolify_uuid

        # --- ETAPE 2 : L'ENVIRONNEMENT ---
        if not self.coolify_env_uuid:
            self._create_coolify_environment(project_uuid)

        # --- ETAPE 3 : LE SERVICE (Docker Compose) ---
        self._create_coolify_service()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Provisioning Réussi'),
                'message': _('La stack complète (Projet > Env > Service) a été initialisée.'),
                'type': 'success',
                'sticky': True,
            }
        }

    def _create_coolify_environment(self, project_uuid):
        """ Crée l'environnement (ex: 'production') DANS le projet """
        base_url, token = self._get_api_config()
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        # Nom de l'environnement (ex: 'production', 'staging')
        env_name = self.env_type

        payload = {
            "name": env_name,
            "project_uuid": project_uuid
        }

        # Endpoint hypothétique : POST /projects/{uuid}/environments
        # Vérifiez la doc API Coolify exacte, parfois c'est POST /environments avec project_uuid dans le body
        url = f"{base_url}/api/v1/projects/{project_uuid}/environments"

        try:
            res = requests.post(url, json=payload, headers=headers)
            if res.status_code in [200, 201]:
                data = res.json()
                self.coolify_env_uuid = data.get('uuid')
                self.message_post(body=_("Environnement Coolify '%s' créé.") % env_name)
            else:
                raise UserError(_("Impossible de créer l'environnement : %s") % res.text)
        except Exception as e:
            raise UserError(str(e))

    def _create_coolify_service(self):
        """ Crée le service final via Docker Compose """

        # 1. Récupérer le template depuis la licence
        valid_license = self.instance_id.license_ids.filtered(lambda l: l.state == 'valid')[:1]
        if not valid_license:
            raise UserError(_("Pas de licence valide pour récupérer le template Docker."))

        template = valid_license.type_id.docker_compose_template
        if not template:
            raise UserError(_("Template Docker vide sur le type de licence."))

        # 2. Templating
        compose_content = template.replace('${DOMAIN_URL}', self.domain_url or 'localhost')
        compose_content = compose_content.replace('${DB_PASSWORD}', self.odoo_master_password or 'admin')

        # Mise à jour locale
        self.docker_compose = compose_content

        # 3. Envoi API
        base_url, token = self._get_api_config()
        headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

        # On a besoin de l'UUID du serveur physique où déployer
        server_uuid = self.instance_id.server_id.coolify_uuid  # Assurez-vous d'avoir ajouté ce champ sur saas.server !
        if not server_uuid:
            raise UserError(_("Le serveur physique sélectionné n'a pas d'UUID Coolify configuré."))

        # Payload pour créer un service
        payload = {
            "type": "docker-compose",
            "name": f"Odoo {self.name}",
            "project_uuid": self.instance_id.coolify_uuid,
            "environment_uuid": self.coolify_env_uuid,
            "server_uuid": server_uuid,
            "docker_compose_raw": compose_content
        }

        url = f"{base_url}/api/v1/applications/docker-compose"  # Endpoint probable pour v4

        try:
            res = requests.post(url, json=payload, headers=headers)
            if res.status_code in [200, 201]:
                data = res.json()
                self.coolify_uuid = data.get('uuid')
                self.state = 'starting'
                self.message_post(body=_("Service Docker créé avec succès. UUID: %s") % self.coolify_uuid)

                # Déclencher le déploiement immédiat
                self._coolify_request('POST', f"deploy?uuid={self.coolify_uuid}")
            else:
                raise UserError(_("Échec création Service : %s") % res.text)
        except Exception as e:
            raise UserError(str(e))

    def action_magic_login(self):
        self.ensure_one()
        if not self.domain_url:
            raise UserError(_("Pas d'URL définie pour cet environnement."))

        # SÉCURITÉ RENFORCÉE ICI
        if not self.audit_token or len(self.audit_token) < 8:
            raise UserError(_("Le Token d'Audit est vide ou trop court. Veuillez configurer un secret fort."))

        # On utilise le token d'audit comme clé secrète partagée
        secret = self.audit_token
        if not secret:
            raise UserError(_("Le Token d'Audit (Agent) n'est pas configuré. Il sert de clé secrète pour le SSO."))

        # Création du payload
        timestamp = int(time.time())
        # Le token est : timestamp + signature
        # Signature = SHA256(timestamp + secret)
        signature = hashlib.sha256(f"{timestamp}{secret}".encode('utf-8')).hexdigest()

        # URL cible
        target_url = f"{self.domain_url.rstrip('/')}/egidix/sso?ts={timestamp}&sig={signature}"

        return {
            'type': 'ir.actions.act_url',
            'url': target_url,
            'target': 'new',
        }