# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import UserError

ACTIVITY_TYPE_SELECTION = [
    ('land_prep', 'Land Preparation'),
    ('sowing', 'Sowing'),
    ('irrigation', 'Irrigation'),
    ('fertilization', 'Fertilization'),
    ('spraying', 'Spraying'),
    ('weeding', 'Weeding'),
    ('harvest', 'Harvest'),
    ('other', 'Other'),
]

STATE_SELECTION = [
    ('draft', 'Draft'),
    ('done', 'Done'),
    ('cancelled', 'Cancelled'),
]


class AgriFieldActivity(models.Model):
    _name = 'agri.field.activity'
    _description = 'Field Activity'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(default='New', copy=False, tracking=True)
    activity_type = fields.Selection(ACTIVITY_TYPE_SELECTION, required=True, tracking=True)
    date = fields.Date(required=True, default=fields.Date.context_today, tracking=True)
    state = fields.Selection(STATE_SELECTION, default='draft', required=True, tracking=True)

    field_id = fields.Many2one('agri.field', string='Field', required=True, tracking=True)
    farm_id = fields.Many2one(related='field_id.farm_id', store=True, readonly=True)
    company_id = fields.Many2one(related='field_id.company_id', store=True, readonly=True)
    currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)
    crop_plan_id = fields.Many2one(
        'agri.crop.plan', string='Crop Plan',
        domain="[('field_id', '=', field_id)]",
    )

    material_line_ids = fields.One2many('agri.field.activity.material', 'activity_id', string='Materials Used')
    labor_line_ids = fields.One2many('agri.field.activity.labor', 'activity_id', string='Labour')
    machinery_line_ids = fields.One2many('agri.field.activity.machinery', 'activity_id', string='Machinery')

    material_cost = fields.Monetary(currency_field='currency_id', compute='_compute_costs', store=True)
    labor_cost = fields.Monetary(currency_field='currency_id', compute='_compute_costs', store=True)
    machinery_cost = fields.Monetary(currency_field='currency_id', compute='_compute_costs', store=True)
    total_cost = fields.Monetary(currency_field='currency_id', compute='_compute_costs', store=True)

    stock_move_ids = fields.One2many('stock.move', 'agri_field_activity_id', string='Stock Moves')
    stock_move_count = fields.Integer(compute='_compute_stock_move_count')

    notes = fields.Text(string='Notes')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('agri.field.activity') or 'New'
        return super().create(vals_list)

    @api.depends(
        'material_line_ids.amount', 'labor_line_ids.amount', 'machinery_line_ids.amount',
    )
    def _compute_costs(self):
        for activity in self:
            activity.material_cost = sum(activity.material_line_ids.mapped('amount'))
            activity.labor_cost = sum(activity.labor_line_ids.mapped('amount'))
            activity.machinery_cost = sum(activity.machinery_line_ids.mapped('amount'))
            activity.total_cost = activity.material_cost + activity.labor_cost + activity.machinery_cost

    @api.depends('stock_move_ids')
    def _compute_stock_move_count(self):
        for activity in self:
            activity.stock_move_count = len(activity.stock_move_ids)

    def _get_source_location(self):
        self.ensure_one()
        warehouse = self.field_id.farm_id.warehouse_id
        if not warehouse:
            warehouse = self.env['stock.warehouse'].search(
                [('company_id', '=', self.company_id.id)], limit=1,
            )
        if not warehouse:
            raise UserError('No warehouse configured for farm "%s". Set one on the farm, '
                             'or create a warehouse for company "%s".'
                             % (self.field_id.farm_id.name, self.company_id.name))
        return warehouse.lot_stock_id

    def _get_destination_location(self):
        return self.env.ref('leapai_agriculture.stock_location_field_consumption')

    def _create_stock_moves(self):
        self.ensure_one()
        moves = self.env['stock.move']
        if not self.material_line_ids:
            return moves
        source_location = self._get_source_location()
        dest_location = self._get_destination_location()
        for line in self.material_line_ids.filtered(lambda l: not l.stock_move_id and l.product_uom_qty):
            move = self.env['stock.move'].create({
                'product_id': line.product_id.id,
                'product_uom_qty': line.product_uom_qty,
                'product_uom': line.product_uom_id.id or line.product_id.uom_id.id,
                'location_id': source_location.id,
                'location_dest_id': dest_location.id,
                'company_id': self.company_id.id,
                'origin': self.name,
                'agri_field_activity_id': self.id,
            })
            move._action_confirm()
            move._action_assign()
            move._set_quantity_done(line.product_uom_qty)
            move.picked = True
            move._action_done()
            line.stock_move_id = move.id
            moves |= move
        return moves

    def action_done(self):
        for activity in self:
            if activity.state != 'draft':
                continue
            activity._create_stock_moves()
            for line in activity.labor_line_ids:
                if not line.hourly_cost and line.employee_id:
                    line.hourly_cost = line.employee_id.agri_hourly_cost
            for line in activity.machinery_line_ids:
                if not line.hourly_cost and line.equipment_id:
                    line.hourly_cost = line.equipment_id.agri_hourly_cost
            activity.state = 'done'

    def action_cancel(self):
        for activity in self:
            activity.stock_move_ids.filtered(lambda m: m.state not in ('done', 'cancel'))._action_cancel()
            activity.state = 'cancelled'

    def action_set_draft(self):
        self.write({'state': 'draft'})

    def action_view_stock_moves(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Stock Moves',
            'res_model': 'stock.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.stock_move_ids.ids)],
        }


class AgriFieldActivityMaterial(models.Model):
    _name = 'agri.field.activity.material'
    _description = 'Field Activity Material Line'

    activity_id = fields.Many2one('agri.field.activity', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_uom_qty = fields.Float(string='Quantity', required=True, default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure')
    unit_cost = fields.Float(string='Unit Cost', compute='_compute_unit_cost', store=True, readonly=False)
    amount = fields.Monetary(
        string='Subtotal', currency_field='currency_id', compute='_compute_amount', store=True,
    )
    currency_id = fields.Many2one(related='activity_id.currency_id')
    stock_move_id = fields.Many2one('stock.move', string='Stock Move', readonly=True, copy=False)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        for line in self:
            if line.product_id:
                line.product_uom_id = line.product_id.uom_id

    @api.depends('product_id')
    def _compute_unit_cost(self):
        for line in self:
            line.unit_cost = line.product_id.standard_price

    @api.depends('product_uom_qty', 'unit_cost')
    def _compute_amount(self):
        for line in self:
            line.amount = line.product_uom_qty * line.unit_cost


class AgriFieldActivityLabor(models.Model):
    _name = 'agri.field.activity.labor'
    _description = 'Field Activity Labour Line'

    activity_id = fields.Many2one('agri.field.activity', required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True)
    hours = fields.Float(string='Hours', required=True, default=1.0)
    hourly_cost = fields.Float(string='Hourly Cost')
    amount = fields.Monetary(
        string='Subtotal', currency_field='currency_id', compute='_compute_amount', store=True,
    )
    currency_id = fields.Many2one(related='activity_id.currency_id')

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        for line in self:
            if line.employee_id:
                line.hourly_cost = line.employee_id.agri_hourly_cost

    @api.depends('hours', 'hourly_cost')
    def _compute_amount(self):
        for line in self:
            line.amount = line.hours * line.hourly_cost


class AgriFieldActivityMachinery(models.Model):
    _name = 'agri.field.activity.machinery'
    _description = 'Field Activity Machinery Line'

    activity_id = fields.Many2one('agri.field.activity', required=True, ondelete='cascade')
    equipment_id = fields.Many2one(
        'maintenance.equipment', string='Equipment', required=True,
        domain="[('is_agri_machinery', '=', True)]",
    )
    hours = fields.Float(string='Hours', required=True, default=1.0)
    hourly_cost = fields.Float(string='Hourly Cost')
    amount = fields.Monetary(
        string='Subtotal', currency_field='currency_id', compute='_compute_amount', store=True,
    )
    currency_id = fields.Many2one(related='activity_id.currency_id')

    @api.onchange('equipment_id')
    def _onchange_equipment_id(self):
        for line in self:
            if line.equipment_id:
                line.hourly_cost = line.equipment_id.agri_hourly_cost

    @api.depends('hours', 'hourly_cost')
    def _compute_amount(self):
        for line in self:
            line.amount = line.hours * line.hourly_cost
