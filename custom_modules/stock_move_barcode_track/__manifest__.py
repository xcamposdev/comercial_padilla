# -*- coding: utf-8 -*-
{
    'name': "Stock Move Barcode Sale Track Custom",
    'summary': """
        This module extends the barcode module functionality to redirect to a Sale by barcode""",
    'description': """
        This module extends the barcode module functionality to redirect to a Sale by barcode
    """,
    'version': '1.0.0.0',
    'author': 'Develoop Software S.A.',
    'category': 'Padilla',
    'website': 'https://www.develoop.net/',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'stock_barcode'],

    # always loaded
    'data': [
        'data/paperformat.xml',
        'views/views.xml',
    ],
   'images': ['static/description/icon.png'],
   'installable': True,
}
