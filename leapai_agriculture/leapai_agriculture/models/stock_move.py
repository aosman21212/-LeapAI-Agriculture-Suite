# -*- coding: utf-8 -*-
from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    agri_field_activity_id = fields.Many2one(
        'agri.field.activity', string='Field Activity', index='btree_not_null',
    )
