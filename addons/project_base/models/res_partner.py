# -*- coding: utf-8 -*-

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    ice = fields.Char(string="ICE")
    siret = fields.Char(string='SIRET', size=14)
    ape = fields.Char(string='APE')
