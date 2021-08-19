# -*- coding: utf-8 -*-

{
    'name': "Barcode Custom",
    'summary': "Use barcode scanners to process logistics operations",
    'description': """
This module enables the barcode scanning feature for the warehouse management system.
    """,
    'category': 'Operations/Inventory',
    'version': '1.0',
    'depends': ['base', 'web', 'barcodes', 'stock', 'web_tour', 'sale', 'padilla_tss_partner_custom'],
    'data': [
        'views/stock_inventory_views.xml',
        'views/stock_picking_views.xml',
        'views/stock_move_line_views.xml',
        'views/stock_barcode_templates.xml',
        'views/stock_barcode_views.xml',
        'views/res_config_settings_views.xml',
        'views/stock_scrap_views.xml',
        'views/stock_location_views.xml',
        'wizard/stock_barcode_lot_view.xml',
        'views/stock_warehouse.xml',
        'views/stock_move.xml',
        'data/data.xml',
        'views/product_packaging.xml',
        'views/stock_quant.xml',
    ],
    'qweb': [
        "static/src/xml/stock_barcode.xml",
        "static/src/xml/qweb_templates.xml",
        "static/src/xml/qweb_templates_custom.xml",
    ],
    'demo': [
        'data/demo.xml',
    ],
    'installable': True,
    'application': True
}
