from odoo import http, fields
from odoo.http import request
from odoo import _
import logging

_logger = logging.getLogger(__name__)


class SaasTelemetryController(http.Controller):

    @http.route('/api/saas/telemetry', type='json', auth='public', methods=['POST'], csrf=False)
    def receive_telemetry(self, token, db_uuid, users_count, modules_list):
        """
        Endpoint called by client instances.
        Receives: License Token, Unique DB UUID, Metrics.
        Returns: Status (valid/expired/fraud), Expiration Date, Message.
        """
        # 1. Get the real IP of the requester (Anti-Fraud)
        # If behind a proxy (Nginx), Odoo must be configured to read X-Forwarded-For
        client_ip = request.httprequest.remote_addr

        # 2. Find the license via the Token
        License = request.env['saas.license'].sudo()
        license_rec = License.search([('token', '=', token)], limit=1)

        response = {
            'status': 'fraud',
            'message': _('Invalid or unknown license.'),
            'expiration_date': False
        }

        if not license_rec:
            # Logs are usually kept in English for admins/devs
            _logger.warning(f"⚠️ Unknown connection attempt from IP: {client_ip} with Token: {token}")
            return response

        # 3. Update technical info (Monitoring)
        # We record the IP and UUID to detect if the code was copied elsewhere
        cluster = license_rec.cluster_id

        # Fraud Detection: If the IP changed drastically or if the DB UUID is new
        # We update the info so you can see it in the backend
        server = cluster.server_id
        if server.ssh_ip != client_ip:
            # Use _() here so the message in the chatter can be translated
            cluster.message_post(
                body=_("🚨 ALERT: IP change detected! Old: {old_ip} -> New: {new_ip}").format(
                    old_ip=server.ssh_ip,
                    new_ip=client_ip
                )
            )
            # Optional: Automatically block if IP changes
            # server.ssh_ip = client_ip # Or update if we are lenient

        # Store audit info
        license_rec.write({
            'last_audit_date': fields.Datetime.now(),
            'compliance_details': f"IP: {client_ip}<br/>DB UUID: {db_uuid}<br/>Users: {users_count}",
            # Verify quotas here
            'compliance_status': 'compliant' if users_count <= license_rec.max_users else 'fraud'
        })

        # 4. Final Decision
        today = fields.Date.today()

        if license_rec.state == 'expired' or license_rec.date_end < today:
            response['status'] = 'expired'
            response['message'] = _('Your license has expired. Please renew.')
        elif users_count > license_rec.max_users and license_rec.max_users > 0:
            response['status'] = 'fraud'
            response['message'] = _('Quota exceeded: {count}/{max} users.').format(
                count=users_count,
                max=license_rec.max_users
            )
        else:
            response['status'] = 'valid'
            response['message'] = _('License active.')
            response['expiration_date'] = str(license_rec.date_end)

        return response