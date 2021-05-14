odoo.define('product_packaging_custom.abstract_client_action_custom_js', function (require) {
    "use strict";
    
    var StockBarcodeClientAction = require("stock_barcode.ClientAction");
    var core = require('web.core');
    var _t = core._t;

    StockBarcodeClientAction.include({
        _step_product: function (barcode, linesActions) {
            console.log("PRODUCTOS NUEVO");//andres
            barcode = "3057067316251";
            console.log(this);
            console.log(this.currentState.picking_type_code);
            
            var self = this;
            this.currentStep = 'product';
            var errorMessage;
    
            var product = this._isProduct(barcode);
            if (product) {
                if (product.tracking !== 'none') {
                    this.currentStep = 'lot';
                }
                var res = this._incrementLines({'product': product, 'barcode': barcode});
                if (res.isNewLine) {
                    if (this.actionParams.model === 'stock.inventory') {
                        // FIXME sle: add owner_id, prod_lot_id, owner_id, product_uom_id
                        return this._rpc({
                            model: 'product.product',
                            method: 'get_theoretical_quantity',
                            args: [
                                res.lineDescription.product_id.id,
                                res.lineDescription.location_id.id,
                            ],
                        }).then(function (theoretical_qty) {
                            res.lineDescription.theoretical_qty = theoretical_qty;
                            linesActions.push([self.linesWidget.addProduct, [res.lineDescription, self.actionParams.model]]);
                            self.scannedLines.push(res.id || res.virtualId);
                            return Promise.resolve({linesActions: linesActions});
                        });
                    } else {
                        linesActions.push([this.linesWidget.addProduct, [res.lineDescription, this.actionParams.model]]);
                    }
                } else {
                    //--------------------------------------------------------------
                    if (res.lineDescription != null && product.x_location != null && product.x_location_usage != null &&
                        this.currentState.picking_type_code == "internal" && res.lineDescription.location_dest_id.id != product.x_location[0])
                    {
                        errorMessage = 'El producto seleccionado se encuentra en la ubicación ' + product.x_location[1] + ', esta ubicacion es distinta a ' + res.lineDescription.location_dest_id.display_name;
                        return Promise.reject(errorMessage);
                    }
                    //--------------------------------------------------------------
                    if (product.tracking === 'none') {
                        linesActions.push([this.linesWidget.incrementProduct, [res.id || res.virtualId, product.qty || 1, this.actionParams.model]]);
                    } else {
                        linesActions.push([this.linesWidget.incrementProduct, [res.id || res.virtualId, 0, this.actionParams.model]]);
                    }
                }
                this.scannedLines.push(res.id || res.virtualId);
                return Promise.resolve({linesActions: linesActions});
            } else {
                var success = function (res) {
                    return Promise.resolve({linesActions: res.linesActions});
                };
                var fail = function (specializedErrorMessage) {
                    self.currentStep = 'product';
                    if (specializedErrorMessage){
                        return Promise.reject(specializedErrorMessage);
                    }
                    if (! self.scannedLines.length) {
                        if (self.groups.group_tracking_lot) {
                            errorMessage = _t("You are expected to scan one or more products or a package available at the picking's location");
                        } else {
                            errorMessage = _t('You are expected to scan one or more products.');
                        }
                        return Promise.reject(errorMessage);
                    }
    
                    var destinationLocation = self.locationsByBarcode[barcode];
                    if (destinationLocation) {
                        return self._step_destination(barcode, linesActions);
                    } else {
                        errorMessage = _t('You are expected to scan more products or a destination location.');
                        return Promise.reject(errorMessage);
                    }
                };
                return self._step_lot(barcode, linesActions).then(success, function () {
                    return self._step_package(barcode, linesActions).then(success, fail);
                });
            }
        },
    });
    return StockBarcodeClientAction;
});