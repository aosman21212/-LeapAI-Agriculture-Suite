# -*- coding: utf-8 -*-
from odoo import api, fields, models

from .agri_field import SOIL_TYPE_SELECTION


class AgriSoilSample(models.Model):
    _name = 'agri.soil.sample'
    _description = 'Soil Sample'
    _order = 'date desc, id desc'

    name = fields.Char(compute='_compute_name', store=True)
    field_id = fields.Many2one('agri.field', string='Field', required=True, ondelete='cascade')
    farm_id = fields.Many2one(related='field_id.farm_id', store=True, readonly=True)
    company_id = fields.Many2one(related='field_id.company_id', store=True, readonly=True)
    date = fields.Date(string='Sample Date', required=True, default=fields.Date.context_today)
    soil_type = fields.Selection(SOIL_TYPE_SELECTION, string='Soil Type')
    ph = fields.Float(string='pH', digits=(4, 2))
    organic_matter = fields.Float(string='Organic Matter (%)', digits=(5, 2))
    nitrogen = fields.Float(string='Nitrogen (N) mg/kg')
    phosphorus = fields.Float(string='Phosphorus (P) mg/kg')
    potassium = fields.Float(string='Potassium (K) mg/kg')
    ec = fields.Float(string='Electrical Conductivity (EC) dS/m', digits=(6, 2))
    notes = fields.Text(string='Notes')

    @api.depends('field_id', 'date')
    def _compute_name(self):
        for sample in self:
            sample.name = '%s - %s' % (sample.field_id.name or '', sample.date or '')
