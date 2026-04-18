from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from datetime import date, timedelta
import uuid
import logging

_logger = logging.getLogger(__name__)


class SaasLicense(models.Model):
    _name = 'saas.license'
    _description = 'Active License'
    _rec_name = 'type_id'

    instance_id = fields.Many2one('saas.instance', string="Client Instance", required=True, ondelete='cascade')
    type_id = fields.Many2one('saas.license.type', string="License Type", required=True)
    date_start = fields.Date(string="Start Date", default=fields.Date.today, required=True)
    date_end = fields.Date(string="End Date", compute='_compute_date_end', required=True)

    # Validity Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('valid', 'Valid'),
        ('expired', 'Expired'),
        ('future', 'Future')
    ], string="Status", store=True)

    token = fields.Char(string="Unique Token", default=lambda self: str(uuid.uuid4()), copy=False, readonly=True)

    # Link to associated Quotation/Order
    sale_order_id = fields.Many2one('sale.order', string="Renewal Quotation", readonly=True)

    # To avoid creating 50 renewals for the same license, we point to the next one
    renewal_license_id = fields.Many2one('saas.license', string="Next License (Renewal)", readonly=True)

    @api.depends('type_id', 'date_start')
    def _compute_date_end(self):
        """ Computes the end date automatically based on type duration """
        for rec in self:
            if rec.type_id and rec.date_start:
                months = rec.type_id.duration_months
                if months > 0:
                    # Use relativedelta to handle months correctly (28, 30, 31 days)
                    # Subtract 1 day to make it an exact year (e.g., 01/01/2024 -> 12/31/2024)
                    rec.date_end = rec.date_start + relativedelta(months=months) - relativedelta(days=1)
                else:
                    rec.date_end = False
            else:
                rec.date_end = False

    def action_generate_quotation(self):
        """ Creates an Odoo quotation based on the license type """
        self.ensure_one()
        if self.sale_order_id:
            return  # Quotation already exists

        if not self.type_id.product_id:
            # Check that a product is configured on the license type
            raise models.UserError(_("No billable product is defined on this license type."))

        # Create Quotation
        # Note: We translate the product description line for the customer
        line_name = _("SaaS License Renewal - {} ({} to {})").format(
            self.type_id.name,
            self.date_start,
            self.date_end
        )

        sale_vals = {
            'partner_id': self.instance_id.partner_id.id,
            'origin': _("License {}").format(self.type_id.name),
            'client_order_ref': self.token,  # Link the token
            'order_line': [(0, 0, {
                'product_id': self.type_id.product_id.id,
                'name': line_name,
                'product_uom_qty': 1,
                'price_unit': self.type_id.product_id.lst_price,
            })]
        }

        order = self.env['sale.order'].create(sale_vals)
        self.sale_order_id = order.id

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Quotation Created'),
                'message': _('Quotation {} has been generated.').format(order.name),
                'type': 'success'
            }
        }

    def action_send_quotation_email(self):
        """ Opens email composer with specific SaaS template """
        self.ensure_one()
        if not self.sale_order_id:
            raise models.UserError(_("Please generate the quotation first."))

        # 1. Find our custom template
        template_id = self.env.ref('saas_manager.email_template_saas_renewal').id

        # 2. Prepare context for email composer
        ctx = {
            'default_model': 'sale.order',
            'default_res_ids': [self.sale_order_id.id],
            'default_use_template': True,
            'default_template_id': template_id,
            'force_email': True
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    # --- AUTOMATION (CRON) ---

    @api.model
    def _cron_manage_renewals(self):
        """
        Method called daily by scheduler.
        Checks licenses expiring in 15 days.
        """
        target_date = date.today() + timedelta(days=15)

        # 1. Find licenses expiring exactly in 15 days (or less)
        # And which do NOT have a renewal yet
        expiring_licenses = self.search([
            ('state', '=', 'valid'),
            ('date_end', '=', target_date),
            ('renewal_license_id', '=', False)
        ])

        _logger.info(f"[SaaS Cron] {len(expiring_licenses)} licenses found for renewal.")

        for lic in expiring_licenses:
            try:
                # A. Create the new "Draft" license for the next period
                # Assume 1 year duration by default, or copy previous duration
                duration = lic.date_end - lic.date_start
                new_start = lic.date_end + timedelta(days=1)
                new_end = new_start + duration

                new_license = self.create({
                    'instance_id': lic.instance_id.id,
                    'type_id': lic.type_id.id,
                    'date_start': new_start,
                    'date_end': new_end,
                    'state': 'draft',  # Draft as requested
                })

                # Link old to new to avoid repeating process tomorrow
                lic.renewal_license_id = new_license.id

                # B. Generate quotation on the NEW license
                new_license.action_generate_quotation()

                # C. Send email automatically
                if new_license.sale_order_id:
                    # USE OUR TEMPLATE HERE
                    template = self.env.ref('saas_manager.email_template_saas_renewal')

                    new_license.sale_order_id.with_context(force_send=True).message_post_with_template(
                        template.id,
                        email_layout_xmlid='mail.mail_notification_layout_with_responsible_signature'
                    )

                    # Mark quotation as sent for traceability
                    new_license.sale_order_id.action_quotation_sent()

                _logger.info(
                    f"Auto renewal performed for {lic.instance_id.name} -> Quotation {new_license.sale_order_id.name}")

            except Exception as e:
                _logger.error(f"License renewal error {lic.id}: {str(e)}")

    @api.onchange('date_start', 'date_end')
    def _compute_state(self):
        today = date.today()
        for rec in self:
            if not rec.date_start or not rec.date_end:
                rec.state = 'draft'
                continue

            if rec.date_start > today:
                rec.state = 'future'
            elif rec.date_end < today:
                rec.state = 'expired'
            else:
                rec.state = 'valid'

    def action_view_sale_order(self):
        """ Smart Button to open linked quotation """
        self.ensure_one()
        if not self.sale_order_id:
            return

        return {
            'type': 'ir.actions.act_window',
            'name': _('Quotation / Order'),
            'res_model': 'sale.order',
            'view_mode': 'form',
            'res_id': self.sale_order_id.id,
            'context': {'create': False},
        }