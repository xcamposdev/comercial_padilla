# -*- coding: utf-8 -*-
{
    'name': "Stock Move Barcode Sale Track",
    'summary': """
        This module extends the barcode module functionality to redirect to a Sale by barcode""",
    'description': """
        This module extends the barcode module functionality to redirect to a Sale by barcode
    """,
    'version': '0.1',
    'author': 'Develoop Software S.A.',
    'category': 'Develoop',
    'website': 'https://www.develoop.net/',

    # any module necessary for this one to work correctly
    'depends': ['base', 'web', 'sale', 'stock_barcode'],

    # always loaded
    'data': [
        'static/src/xml/qweb_templates.xml',
        'data/paperformat.xml',
        'views/views.xml',
    ],
    'qweb': [
        'views/mobile_reports_options.xml',
    ],
    'images': ['static/description/icon.png'],
    'demo': [],
    'installable': True,
}
