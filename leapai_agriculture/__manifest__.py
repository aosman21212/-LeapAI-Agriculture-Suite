# -*- coding: utf-8 -*-
# =============================================================================
#  LeapAI Agriculture Suite
# -----------------------------------------------------------------------------
#  Location  : King Abdulaziz Branch Road, Riyadh, Saudi Arabia
#  Email     : sales@leapai.ai
#  Phone     : +966 53 553 3627
#  Website   : https://leapai.ai
#  Developer : Abdulkaraim Osman — Tech Manager | Backend Engineer | DevOps Engineer
#              at Bab International Corp For Specialized Services
#  LinkedIn  : https://www.linkedin.com/in/abdulkaraim-o-385b7a110/
# =============================================================================
{
    'name': 'LeapAI Agriculture Suite',
    'version': '19.0.1.0.0',
    'category': 'Agriculture',
    'summary': 'Farm, field, crop planning, field operations and job costing for agricultural businesses',
    'description': """
LeapAI Agriculture Suite — Phase 1
===================================
Farms, fields and crop planning management:

• Farms & Fields — Register farms, draw field boundaries on an interactive map
  (OpenStreetMap) with automatic area calculation
• Soil Samples — Track soil type, pH, organic matter, NPK and EC over time
• Crops — Master data for varieties, days-to-harvest, expected yield and GDD
• Seasons & Crop Plans — Plan crops per field per season, with overlap
  prevention and budget vs. actual cost tracking
• Field Activities — Land prep, sowing, irrigation, fertilization, spraying,
  weeding and harvest, consuming real stock, employee labour hours and
  machinery/equipment hours
• Job Cost Sheets — Budget vs. actual cost per hectare, per crop plan

This is phase 1 of the suite (crop & field management). Monitoring &
analytics (scouting, weather), livestock management and the contract-farming
portal are planned for later phases.

Contact
-------
Email   : abdzoro89@gmail.com
Website : https://leapai.ai/
    """,
    'author': 'LeapAI',
    'maintainer': 'Abdulkaraim Osman',
    'support': 'sales@leapai.ai',
    'website': 'https://leapai.ai/',
    'license': 'LGPL-3',
    'application': True,
    'depends': ['mail', 'hr', 'stock', 'maintenance', 'uom'],
    'data': [
        'security/agriculture_security.xml',
        'security/ir.model.access.csv',
        'data/agri_stock_data.xml',
        'data/agri_sequence_data.xml',
        'views/agri_farm_views.xml',
        'views/agri_field_views.xml',
        'views/agri_soil_sample_views.xml',
        'views/agri_crop_views.xml',
        'views/agri_crop_plan_views.xml',
        'views/agri_season_views.xml',
        'views/agri_field_activity_views.xml',
        'views/menu.xml',
    ],
    'demo': [
        'demo/demo_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'leapai_agriculture/static/lib/leaflet/leaflet.css',
            'leapai_agriculture/static/lib/leaflet/leaflet.js',
            'leapai_agriculture/static/src/scss/field_map_widget.scss',
            'leapai_agriculture/static/src/js/field_map_widget.js',
            'leapai_agriculture/static/src/xml/field_map_widget.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
}
