{
    'name': 'Restrict new lines in PACK Custom',
    'category': 'Develoop',
    'version': '0.0',
    'summary': """No permite que se carguen nuevas lineas de productos que no sean los requeridos por la APP de 
    codigo de barras.""",
    'description': """""",
    'depends': ['product', 'stock_barcode', 'product_packaging_custom'],
    'data': [
        'views/assets.xml',
    ],
    'author': 'Develoop Software',
    'images': ['static/description/icon.png'],
    'maintainer': 'Develoop Software',
    'website': 'https://www.develoop.net',
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False
}
