# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AgriSeason(models.Model):
    _name = 'agri.season'
    _description = 'Season'
    _order = 'date_start desc'

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company,
    )
    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True)
    crop_plan_ids = fields.One2many('agri.crop.plan', 'season_id', string='Crop Plans')
    crop_plan_count = fields.Integer(compute='_compute_crop_plan_count')
    notes = fields.Text(string='Notes')

    _date_check = models.Constraint(
        'CHECK (date_end >= date_start)',
        'The season end date must be after its start date.',
    )

    @api.depends('crop_plan_ids')
    def _compute_crop_plan_count(self):
        for season in self:
            season.crop_plan_count = len(season.crop_plan_ids)
