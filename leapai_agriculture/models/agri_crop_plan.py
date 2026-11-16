# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('confirmed', 'Confirmed'),
    ('in_progress', 'In Progress'),
    ('harvested', 'Harvested'),
    ('cancelled', 'Cancelled'),
]


class AgriCropPlan(models.Model):
    _name = 'agri.crop.plan'
    _description = 'Crop Plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(compute='_compute_name', store=True)
    season_id = fields.Many2one('agri.season', string='Season', required=True, tracking=True)
    field_id = fields.Many2one('agri.field', string='Field', required=True, tracking=True)
    farm_id = fields.Many2one(
        'agri.farm', string='Farm', related='field_id.farm_id', store=True, readonly=True,
    )
    company_id = fields.Many2one(related='field_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)
    crop_id = fields.Many2one('agri.crop', string='Crop', required=True, tracking=True)
    state = fields.Selection(STATE_SELECTION, default='draft', required=True, tracking=True)

    planned_area = fields.Float(string='Planned Area (ha)', digits=(16, 3))
    sowing_date = fields.Date(string='Sowing Date')
    expected_harvest_date = fields.Date(string='Expected Harvest Date')

    budget_amount = fields.Monetary(string='Budget Cost', currency_field='currency_id')
    field_activity_ids = fields.One2many('agri.field.activity', 'crop_plan_id', string='Field Activities')
    activity_count = fields.Integer(compute='_compute_activity_count')

    actual_cost = fields.Monetary(
        string='Actual Cost', currency_field='currency_id',
        compute='_compute_actual_cost', store=True,
    )
    cost_variance = fields.Monetary(
        string='Variance (Budget - Actual)', currency_field='currency_id',
        compute='_compute_actual_cost', store=True,
    )
    cost_per_hectare = fields.Monetary(
        string='Actual Cost / ha', currency_field='currency_id',
        compute='_compute_actual_cost', store=True,
    )
    budget_per_hectare = fields.Monetary(
        string='Budget / ha', currency_field='currency_id',
        compute='_compute_actual_cost', store=True,
    )

    notes = fields.Text(string='Notes')

    _field_season_uniq = models.Constraint(
        'unique(field_id, season_id)',
        'A field can only have one crop plan per season. Edit the existing plan or pick another season/field.',
    )

    @api.depends('field_id.name', 'crop_id.name', 'season_id.name')
    def _compute_name(self):
        for plan in self:
            plan.name = ' / '.join(filter(None, [plan.field_id.name, plan.crop_id.name, plan.season_id.name])) \
                or 'New Crop Plan'

    @api.depends('field_activity_ids')
    def _compute_activity_count(self):
        for plan in self:
            plan.activity_count = len(plan.field_activity_ids)

    @api.depends(
        'field_activity_ids.total_cost', 'field_activity_ids.state',
        'budget_amount', 'planned_area',
    )
    def _compute_actual_cost(self):
        for plan in self:
            done_activities = plan.field_activity_ids.filtered(lambda a: a.state == 'done')
            actual = sum(done_activities.mapped('total_cost'))
            plan.actual_cost = actual
            plan.cost_variance = plan.budget_amount - actual
            plan.cost_per_hectare = actual / plan.planned_area if plan.planned_area else 0.0
            plan.budget_per_hectare = plan.budget_amount / plan.planned_area if plan.planned_area else 0.0

    @api.constrains('field_id', 'season_id', 'state')
    def _check_overlap(self):
        for plan in self:
            if plan.state == 'cancelled':
                continue
            overlapping = self.search([
                ('id', '!=', plan.id),
                ('field_id', '=', plan.field_id.id),
                ('state', '!=', 'cancelled'),
                ('season_id.date_start', '<=', plan.season_id.date_end),
                ('season_id.date_end', '>=', plan.season_id.date_start),
            ])
            if overlapping:
                raise ValidationError(
                    'Field "%s" already has a crop plan (%s) overlapping this season.'
                    % (plan.field_id.name, overlapping[0].name)
                )

    def action_confirm(self):
        self.write({'state': 'confirmed'})

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_harvested(self):
        self.write({'state': 'harvested'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_set_draft(self):
        self.write({'state': 'draft'})

    def action_view_activities(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Field Activities',
            'res_model': 'agri.field.activity',
            'view_mode': 'list,form',
            'domain': [('crop_plan_id', '=', self.id)],
            'context': {
                'default_crop_plan_id': self.id,
                'default_field_id': self.field_id.id,
            },
        }
