odoo.define('product_packaging_custom.picking_client_action_custom_js', function (require) {
    "use strict";
    
    var PickingClientAction = require("stock_barcode.picking_client_action");
    
    PickingClientAction.include({
        _makeNewLine: function (product, barcode, qty_done, package_id, result_package_id) {
            var virtualId = this._getNewVirtualId();
            var currentPage = this.pages[this.currentPageIndex];
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

                'x_product_packaging_id': product.packaging_id,
                'x_product_packaging_qty': qty_done,
            };
            return newLine;
        },
        // _onValidate: function (ev) {
        //     ev.stopPropagation();
        //     console.log(this);
        //     if (this.set_location_dest_barcode != undefined)
        //     {
        //         console.log("this.set_location_dest_barcode");
        //         console.log(this.set_location_dest_barcode);
        //         this._onBarcodeScanned(this.set_location_dest_barcode);
        //     }
        //     else
        //     {
        //         this._validate();
        //     }
        // },

        _applyChanges: function (changes) {
            var formattedCommands = [];
            var cmd = [];
            for (var i in changes) {
                var line = changes[i];
                if (line.id) {
                    // Line needs to be updated
                    cmd = [1, line.id, {
                        'qty_done' : line.qty_done,
                        'location_id': line.location_id.id,
                        'location_dest_id': line.location_dest_id.id,
                        'lot_id': line.lot_id && line.lot_id[0],
                        'lot_name': line.lot_name,
                        'package_id': line.package_id ? line.package_id[0] : false,
                        'result_package_id': line.result_package_id ? line.result_package_id[0] : false,
                        'x_product_packaging_id': line.x_product_packaging_id ? line.x_product_packaging_id : false,
                        'x_product_packaging_qty': line.x_product_packaging_qty ? line.x_product_packaging_qty : false,
                    }];
                    formattedCommands.push(cmd);
                } else {
                    // Line needs to be created
                    cmd = [0, 0, {
                        'picking_id': line.picking_id,
                        'product_id':  line.product_id.id,
                        'product_uom_id': line.product_uom_id[0],
                        'qty_done': line.qty_done,
                        'location_id': line.location_id.id,
                        'location_dest_id': line.location_dest_id.id,
                        'lot_name': line.lot_name,
                        'lot_id': line.lot_id && line.lot_id[0],
                        'state': 'assigned',
                        'package_id': line.package_id ? line.package_id[0] : false,
                        'result_package_id': line.result_package_id ? line.result_package_id[0] : false,
                        'x_product_packaging_id': line.x_product_packaging_id ? line.x_product_packaging_id : false,
                        'x_product_packaging_qty': line.x_product_packaging_qty ? line.x_product_packaging_qty : false,
                        'dummy_id': line.virtual_id,
                    }];
                    formattedCommands.push(cmd);
                }
            }
            if (formattedCommands.length > 0){
                var params = {
                    'mode': 'write',
                    'model_name': this.actionParams.model,
                    'record_id': this.currentState.id,
                    'write_vals': formattedCommands,
                    'write_field': 'move_line_ids',
                };
                return this._rpc({
                    'route': '/stock_barcode/get_set_barcode_view_state',
                    'params': params,
                });
            } else {
                return Promise.reject();
            }
        },

    });
    return PickingClientAction;
});