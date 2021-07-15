# -*- coding: utf-8 -*-
{
    'name': "Stock Move Barcode Sale Track",
    'summary': """
        This module extends the barcode module functionality to redirect to a Sale by barcode""",
    'description': """
        This module extends the barcode module functionality to redirect to a Sale by barcode
    """,
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale', 'stock_barcode'],

    # always loaded
    'data': [
        'data/paperformat.xml',
        'views/views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}
