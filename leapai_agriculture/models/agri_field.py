# -*- coding: utf-8 -*-
import json
import math

from odoo import api, fields, models
from odoo.exceptions import UserError

SOIL_TYPE_SELECTION = [
    ('clay', 'Clay'),
    ('sandy', 'Sandy'),
    ('silty', 'Silty'),
    ('loamy', 'Loamy'),
    ('peaty', 'Peaty'),
    ('chalky', 'Chalky'),
]


class AgriField(models.Model):
    _name = 'agri.field'
    _description = 'Field'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    farm_id = fields.Many2one(
        'agri.farm', string='Farm', required=True, ondelete='cascade', tracking=True,
    )
    company_id = fields.Many2one(related='farm_id.company_id', store=True, readonly=True)

    # --- Boundary / map -----------------------------------------------
    boundary_geojson = fields.Text(
        string='Boundary (GeoJSON)',
        help='Polygon boundary of the field, drawn on the map, stored as GeoJSON coordinates.',
    )
    area = fields.Float(
        string='Area (ha)', digits=(16, 3), tracking=True,
        help='Field area in hectares. Automatically computed when a boundary is drawn on the map, '
             'or can be entered manually.',
    )
    center_latitude = fields.Float(string='Latitude', digits=(16, 6))
    center_longitude = fields.Float(string='Longitude', digits=(16, 6))

    # --- Soil -----------------------------------------------------------
    soil_sample_ids = fields.One2many('agri.soil.sample', 'field_id', string='Soil Samples')
    soil_sample_count = fields.Integer(compute='_compute_soil_sample_count')
    soil_type = fields.Selection(SOIL_TYPE_SELECTION, string='Soil Type')
    last_soil_ph = fields.Float(string='Last pH', related='latest_soil_sample_id.ph', readonly=True)
    last_soil_sample_date = fields.Date(string='Last Soil Sample', related='latest_soil_sample_id.date', readonly=True)
    latest_soil_sample_id = fields.Many2one(
        'agri.soil.sample', compute='_compute_latest_soil_sample', string='Latest Soil Sample',
    )

    # --- Crop planning ----------------------------------------------------
    crop_plan_ids = fields.One2many('agri.crop.plan', 'field_id', string='Crop Plans')
    crop_plan_count = fields.Integer(compute='_compute_crop_plan_count')
    current_crop_plan_id = fields.Many2one(
        'agri.crop.plan', compute='_compute_current_crop_plan', string='Current Crop Plan',
    )
    current_crop_id = fields.Many2one(related='current_crop_plan_id.crop_id', string='Current Crop', readonly=True)

    notes = fields.Html(string='Notes')

    @api.depends('soil_sample_ids')
    def _compute_soil_sample_count(self):
        for field in self:
            field.soil_sample_count = len(field.soil_sample_ids)

    @api.depends('soil_sample_ids.date')
    def _compute_latest_soil_sample(self):
        for field in self:
            samples = field.soil_sample_ids.sorted(key=lambda s: s.date or fields.Date.today(), reverse=True)
            field.latest_soil_sample_id = samples[:1]

    @api.depends('crop_plan_ids')
    def _compute_crop_plan_count(self):
        for field in self:
            field.crop_plan_count = len(field.crop_plan_ids)

    @api.depends('crop_plan_ids.state', 'crop_plan_ids.season_id.date_start', 'crop_plan_ids.season_id.date_end')
    def _compute_current_crop_plan(self):
        today = fields.Date.today()
        for field in self:
            current = field.crop_plan_ids.filtered(
                lambda p: p.state in ('confirmed', 'in_progress')
                and (not p.season_id.date_start or p.season_id.date_start <= today)
                and (not p.season_id.date_end or p.season_id.date_end >= today)
            )
            field.current_crop_plan_id = current[:1]

    def action_compute_area_from_boundary(self):
        """Recompute the field area (hectares) from its GeoJSON boundary polygon
        using an equirectangular projection approximation and the shoelace formula."""
        for field in self:
            if not field.boundary_geojson:
                raise UserError('Draw a boundary on the map before computing the area.')
            try:
                coords = json.loads(field.boundary_geojson)
            except ValueError as exc:
                raise UserError('Invalid boundary data: %s' % exc) from exc
            field.area = field._area_ha_from_coordinates(coords)

    @api.model
    def _area_ha_from_coordinates(self, coords):
        """coords: list of [lng, lat] pairs describing a closed (or open) polygon ring."""
        if not coords or len(coords) < 3:
            return 0.0
        if coords[0] != coords[-1]:
            coords = coords + [coords[0]]
        lat0 = sum(c[1] for c in coords[:-1]) / (len(coords) - 1)
        earth_radius = 6371000.0  # meters
        lat0_rad = math.radians(lat0)
        points_m = []
        for lng, lat in coords:
            x = math.radians(lng) * earth_radius * math.cos(lat0_rad)
            y = math.radians(lat) * earth_radius
            points_m.append((x, y))
        area_m2 = 0.0
        for i in range(len(points_m) - 1):
            x1, y1 = points_m[i]
            x2, y2 = points_m[i + 1]
            area_m2 += (x1 * y2) - (x2 * y1)
        area_m2 = abs(area_m2) / 2.0
        return round(area_m2 / 10000.0, 3)  # m2 -> hectares

    def action_view_crop_plans(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Crop Plans',
            'res_model': 'agri.crop.plan',
            'view_mode': 'list,form',
            'domain': [('field_id', '=', self.id)],
            'context': {'default_field_id': self.id},
        }

    def action_view_soil_samples(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Soil Samples',
            'res_model': 'agri.soil.sample',
            'view_mode': 'list,form',
            'domain': [('field_id', '=', self.id)],
            'context': {'default_field_id': self.id},
        }
