# -*- coding: utf-8 -*-
from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    agri_hourly_cost = fields.Float(
        string='Agriculture Hourly Cost',
        help='Default labour cost per hour used when logging field activity hours for this employee.',
    )
