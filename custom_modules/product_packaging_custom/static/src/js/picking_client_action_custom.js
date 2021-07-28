odoo.define('product_packaging_custom.picking_client_action_custom_js', function (require) {
    "use strict";
    
    var PickingClientAction = require("stock_barcode.picking_client_action");
    
    PickingClientAction.include({
        willStart: function () {
            var self = this;
            var res = this._super.apply(this, arguments);
            res.then(function() {
                // Get the usage of the picking type of `this.picking_id` to chose the mode between
                // `receipt`, `internal`, `delivery`.
                var prom = self._has_origin_picking(self.currentState.id);
                prom.then(function(has_origin){
                    var picking_type_code = self.currentState.picking_type_code;
                    var picking_state = self.currentState.state;

                    self.has_origin = has_origin;

                    if (picking_type_code === 'incoming') {
                        self.mode = 'receipt';
                    } else if (picking_type_code === 'outgoing') {
                        self.mode = 'delivery';
                    } else {
                        self.mode = 'internal';
                    }

                    if (self.currentState.group_stock_multi_locations === false) {
                        self.mode = 'no_multi_locations';
                    }

                    if (picking_state === 'done') {
                        self.mode = 'done';
                    } else if (picking_state === 'cancel') {
                        self.mode = 'cancel';
                    }
                    self.allow_scrap = (
                        (picking_type_code === 'incoming') && (picking_state === 'done') ||
                        (picking_type_code === 'outgoing') && (picking_state !== 'done') ||
                        (picking_type_code === 'internal')
                    )
                });
            });
            return res;
        },
        _has_origin_picking: async function(id) {
            var self = this;
            const response = await self._rpc({
                    model: 'stock.picking',
                    method: 'has_origin',
                    args: [id],
                });
            return response;
        },
        _makeNewLine: function (product, barcode, qty_done, package_id, result_package_id, owner_id) {
            var virtualId = this._getNewVirtualId();
            var currentPage = this.pages[this.currentPageIndex];
            var location_dest_id = currentPage.location_dest_id;
            var location_display_name = currentPage.location_dest_name;
            if (!this.has_origin && product.x_location != undefined && this.currentState.picking_type_code == "internal") {
                location_dest_id = product.x_location[0];
                location_display_name = product.x_location[1];
            }
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
                    'id': location_dest_id,
                    'display_name': location_display_name,
                },
                'package_id': package_id,
                'result_package_id':  (product.x_package != undefined && this.currentState.picking_type_code == "internal") ? [product.x_package[0], product.x_package[1]] : result_package_id,
                'owner_id': owner_id,
                'state': 'assigned',
                'reference': this.name,
                'virtual_id': virtualId,
            };
            return newLine;
        },
    });
    return PickingClientAction;
});