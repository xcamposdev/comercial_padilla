{
    'name': 'Product Packaging Custom',
    'category': 'Sales',
    'version': '0.0',
    'summary': """Permite asociar un empaquetado a un paquete con su ubicación.""",
    'description': """""",
    'depends': ['product',"stock","stock_barcode"],
    'data': [
        'views/product_packaging.xml',
        'views/stock_quant.xml',
        'views/assets.xml',
    ],
    'qweb': ['static/src/xml/qweb_templates.xml'],
    'author': 'Develoop Software',
    'images': ['static/description/icon.png'],
    'maintainer': 'Develoop Software',
    'website': 'https://www.develoop.net',
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False
}
