odoo.define('barcode_restrict_pack_custom.picking_client_action_custom', function (require) {
    "use strict";
    
    var PickingClientAction = require("stock_barcode.picking_client_action");
    
    PickingClientAction.include({
        _getProductBarcodes: function () {
            var self = this;
            var context = {};
            if (this.actionParams.pickingId != undefined) {
                context['pickingId'] = this.actionParams.pickingId;
            };
            return this._rpc({
                'model': 'product.product',
                'method': 'get_all_products_by_barcode',
                'args': [context],
            }).then(function (res) {
                self.productsByBarcode = res;
            });
        },
    });
    return PickingClientAction;
});
