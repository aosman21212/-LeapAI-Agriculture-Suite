# -*- coding: utf-8 -*-
from odoo import fields, models


class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    agri_hourly_cost = fields.Float(
        string='Agriculture Hourly Cost',
        help='Default operating cost per hour used when logging field activity machinery hours for this equipment.',
    )
    is_agri_machinery = fields.Boolean(
        string='Usable in Field Activities',
        help='If checked, this equipment can be selected as machinery on field activities.',
    )
