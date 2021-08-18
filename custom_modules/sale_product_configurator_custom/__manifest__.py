# -*- coding: utf-8 -*-
{
    'name': "Sale Product Configurator Custom",
    'version': '0.1',
    'category': 'Develoop',
    'summary': "Configure your products",

    'description': """
Technical module installed when the user checks the "module_sale_product_configurator" setting.
The main purpose is to override the sale_order view to allow configuring products in the SO form.

It also enables the "optional products" feature.
    """,

    'depends': ['sale', 'sale_product_configurator'],
    'data': [
        'views/templates.xml',
    ],
    'author': 'Develoop Software',
    'images': ['static/description/icon.png'],
    'maintainer': 'Develoop Software',
    'website': 'https://www.develoop.net',
    'installable': True,
    'application': False,
    'auto_install': False

}
