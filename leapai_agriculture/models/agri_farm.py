# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AgriFarm(models.Model):
    _name = 'agri.farm'
    _description = 'Farm'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        default=lambda self: self.env.company,
    )
    partner_id = fields.Many2one(
        'res.partner', string='Owner',
        help='Partner that owns or operates this farm.',
    )
    address = fields.Text(string='Address')
    city = fields.Char()
    country_id = fields.Many2one('res.country', string='Country')
    latitude = fields.Float(string='Latitude', digits=(16, 6))
    longitude = fields.Float(string='Longitude', digits=(16, 6))
    field_ids = fields.One2many('agri.field', 'farm_id', string='Fields')
    field_count = fields.Integer(compute='_compute_field_count', string='Fields Count')
    total_area = fields.Float(
        string='Total Area (ha)', compute='_compute_total_area', store=True,
        digits=(16, 3),
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse',
        domain="[('company_id', '=', company_id)]",
        help='Warehouse used as the source of stock for field activities on this farm.',
    )
    manager_id = fields.Many2one('res.users', string='Farm Manager', default=lambda self: self.env.user)
    notes = fields.Html(string='Notes')

    @api.depends('field_ids')
    def _compute_field_count(self):
        for farm in self:
            farm.field_count = len(farm.field_ids)

    @api.depends('field_ids.area')
    def _compute_total_area(self):
        for farm in self:
            farm.total_area = sum(farm.field_ids.mapped('area'))

    def action_view_fields(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Fields',
            'res_model': 'agri.field',
            'view_mode': 'list,form',
            'domain': [('farm_id', '=', self.id)],
            'context': {'default_farm_id': self.id},
        }
