# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name" : 'Product Reference Filter Odoo Custom',
    "summary": "Product Reference Filter.",
    "version": "13.0.0.0.0",
    "category": "",
    "description": "Filtro personalizado de busqueda de producto por referencia de fabricante.",
    "author": "Develoop Software",
    "website": "https://www.develoop.net",
    'depends': ['base', 'product'],
    'data': [
        'views/product_reference_filter_view.xml',
    ],
    "images": ['static/description/icon.png'],
    'auto_install': False,
    'installable': True,
}