from odoo import models, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        """
        Override of order confirmation.
        If the order is linked to a SaaS license, validate it.
        """
        res = super(SaleOrder, self).action_confirm()

        for order in self:
            # Search for licenses linked to this order
            # (Recall: the sale_order_id field is on the saas.license model)
            licenses = self.env['saas.license'].search([
                ('sale_order_id', '=', order.id),
                ('state', '=', 'draft')  # Only those that are still in draft
            ])

            if licenses:
                licenses.action_force_valid()
                # Optional: Post a message in the order chatter
                order.message_post(body=_("SaaS License automatically activated following confirmation."))

        return res