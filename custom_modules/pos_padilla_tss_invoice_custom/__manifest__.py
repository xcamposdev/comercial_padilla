{
    'name': 'Padilla 2 client types invoices custom',
    'category': 'Develoop',
    'version': '0.0',
    'summary': """Extiende la funcionalidad del punto de venta para poder cambiar el informe de impresion para los 2 tipos de clientes Padilla.""",
    'description': """""",
    'depends': ['base', 'point_of_sale', 'padilla_tss_partner_custom', 'l10n_es_pos'],
    'data': [
        'views/assets.xml',
    ],
    'author': 'Develoop Software',
    'images': ['static/description/icon.png'],
    'maintainer': 'Develoop Software',
    'website': 'https://www.develoop.net',
    'demo': [],
    'qweb': ['static/src/xml/pos.xml'],
    'installable': True,
    'application': False,
    'auto_install': False
}
