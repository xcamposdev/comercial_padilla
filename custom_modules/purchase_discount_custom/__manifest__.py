# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
{
    "name": "Descuentos Compra Custom",
    "author": "Develoop",
    "version": "13.0.0.1",
    "category": "Purchase Management",
    "website": "https://www.develoop.net/",
    "depends": ["base", "purchase_stock","purchase_discount"],
    "data": [
        "views/purchase_order.xml",
        "views/res_partner.xml",
        #"views/product_supplierinfo_view.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
    "images": ["static/description/icon.png"],
}
