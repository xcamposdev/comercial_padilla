odoo.define('product_packaging_custom.picking_client_action_custom_js', function (require) {
    "use strict";
    
    var PickingClientAction = require("stock_barcode.picking_client_action");
    
    PickingClientAction.include({
        _makeNewLine: function (product, barcode, qty_done, package_id, result_package_id) {
            var virtualId = this._getNewVirtualId();
            var currentPage = this.pages[this.currentPageIndex];
            console.log(this.currentState.picking_type_code);
            console.log(this);
            console.log(currentPage);
            var newLine = {
                'picking_id': this.currentState.id,
                'product_id': {
                    'id': product.id,
                    'display_name': product.display_name,
                    'barcode': barcode,
                    'tracking': product.tracking,
                },
                'product_barcode': barcode,
                'display_name': product.display_name,
                'product_uom_qty': 0,
                'product_uom_id': product.uom_id,
                'qty_done': qty_done,
                'location_id': {
                    'id': currentPage.location_id,
                    'display_name': currentPage.location_name,
                },
                'location_dest_id': {
                    'id': (product.x_location != undefined && this.currentState.picking_type_code == "internal") ? product.x_location[0] : currentPage.location_dest_id,
                    'display_name': (product.x_location != undefined && this.currentState.picking_type_code == "internal") ? product.x_location[1] : currentPage.location_dest_name,
                },
                'package_id': package_id,
                'result_package_id':  (product.x_package != undefined && this.currentState.picking_type_code == "internal") ? [product.x_package[0], product.x_package[1]] : result_package_id,
                'state': 'assigned',
                'reference': this.name,
                'virtual_id': virtualId,
            };
            return newLine;
        },
    });
    return PickingClientAction;
});