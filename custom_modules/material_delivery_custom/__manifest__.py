# -*- coding: utf-8 -*-
{
    'name': 'Entrega de Material Custom',
    'version': '1.0.0.0',
    'author': 'Develoop Software S.A.',
    'category': 'Padilla',
    'website': 'https://www.develoop.net/',
    'depends': ['base', 'sale','stock'],
    'summary': 'Modifica la funcionalidad de generacion de stock a partir de una venta',
    'description': """
        Modifica la funcionalidad de generacion de stock a partir de una venta
        """,
    'data': [
        'views/stock_warehouse.xml',
        'views/stock_move.xml',
    ],
    'qweb': [
    ],
    'images': ['static/description/icon.png'],
    'demo': [],
    'installable': True,
}
