# -*- coding: utf-8 -*-
from odoo import fields, models


class AgriCrop(models.Model):
    _name = 'agri.crop'
    _description = 'Crop'
    _order = 'name'

    name = fields.Char(string='Crop', required=True)
    variety = fields.Char(string='Variety')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company', string='Company', default=lambda self: self.env.company,
    )
    days_to_harvest = fields.Integer(
        string='Days to Harvest', help='Typical number of days from sowing to harvest.',
    )
    expected_yield = fields.Float(string='Expected Yield', digits=(16, 2))
    yield_uom_id = fields.Many2one('uom.uom', string='Yield Unit of Measure')
    gdd_base_temperature = fields.Float(
        string='GDD Base Temperature (°C)',
        help='Base temperature used for Growing Degree Day calculations.',
    )
    product_id = fields.Many2one(
        'product.product', string='Harvest Product',
        help='Product used to represent the harvested output of this crop in stock/sales.',
    )
    color = fields.Integer(string='Color')
    notes = fields.Html(string='Notes')
