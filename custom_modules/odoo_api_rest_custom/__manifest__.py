# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name" : 'Odoo API Rest',
    "summary": "Solucion API Rest.",
    "version": "13.0.0.0.0",
    "category": "",
    "description": "API Rest para consulta en Odoo.",
    "author": "Develoop Software",
    "website": "https://www.develoop.net",
    'depends': ['base', 'stock', 'sale', 'product'],
    'data': [
        'security/ir.model.access.csv',
        'views/apirest_store_details.xml',
    ],
    "images": ['static/description/icon.png'],
    'auto_install': False,
    'installable': True,
}