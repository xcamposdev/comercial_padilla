# -*- coding: utf-8 -*-
{
    'name': "package barcode so custom",
    'version': '0.1',
    'author': "Develoop Software",
    'category': 'Uncategorized',
    'summary': 'Empaquetar bultos pedido venta',
    'website': "https://www.develoop.net/",
    'description': """
        - Empaquetar bultos pedido venta
        """,
    'depends': ['base', 'web', 'sale', 'stock_barcode', 'stock_move_barcode_track'],
    'data': [
        'data/paperformat.xml',
        'report/menu.xml',
        'report/print_bultos.xml',
        'views/assets.xml',
        'views/sequence.xml',
    ],
    'qweb': [
        'static/src/xml/mobile_reports_option.xml',
    ],
    'demo': [],
    'installable': True,
}
