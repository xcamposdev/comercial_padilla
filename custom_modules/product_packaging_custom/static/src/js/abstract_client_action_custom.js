odoo.define('product_packaging_custom.abstract_client_action_custom_js', function (require) {
    "use strict";
    
    var StockBarcodeClientAction = require("stock_barcode.ClientAction");
    var core = require('web.core');
    var _t = core._t;

    StockBarcodeClientAction.include({
        _step_product: async function (barcode, linesActions) {
            var self = this;
            this.currentStep = 'product';
            var errorMessage;

            var product = await this._isProduct(barcode)
            if (product) {
                if (product.tracking !== 'none' && self.requireLotNumber) {
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
                        //--------------------------------------------------------------
                        if (!self.has_origin && self.currentState.location_dest_id != undefined && product.x_location != undefined && self.currentState.picking_type_code == "internal" && self.currentState.location_dest_id.id != product.x_location[0])
                        {
                            if (self.scannedLines != "")
                            {
                                var index = this._getLines(this.currentState).indexOf(res.lineDescription);
                                if (index !== -1) {
                                    this._getLines(this.currentState).splice(index, 1);
                                }
                                var index = this.pages[this.currentPageIndex].lines.indexOf(res.lineDescription);
                                if (index !== -1) {
                                    this.pages[this.currentPageIndex].lines.splice(index, 1);
                                }
                                //this._getLines(this.currentState).push(line);
                                //this.pages[this.currentPageIndex].lines.push(line);
                                errorMessage = 'El producto seleccionado se encuentra en la ubicación ' + product.x_location[1] + ', esta ubicacion es distinta a ' + self.currentState.location_dest_id.display_name;
                                return Promise.reject(errorMessage);    
                            }
                            else
                            {
                                res.lineDescription['location_dest_id'] = {
                                    'id': product.x_location[0],
                                    'display_name': product.x_location[1],
                                };
                                res.lineDescription['result_package_id'] = [product.x_package[0], product.x_package[1]];

                                if (product.x_location_barcode)
                                {
                                    var destinationLocation = self.locationsByBarcode[product.x_location_barcode];
                                    if (destinationLocation) {
                                        //self.pages[0].location_dest_id = location_dest_id
                                        // var currentPage = this.pages[0];
                                        // currentPage.location_dest_id = destinationLocation.id
                                        // this.currentState.location_dest_id = destinationLocation;
                                        self.currentState.location_dest_id = destinationLocation;

                                        //self.set_location_dest_barcode = product.x_location_barcode;
                                        var param_write = {};
                                        param_write.args = [[self.currentState.id], {location_dest_id: destinationLocation.id}];
                                        param_write.method = 'write';
                                        param_write.model='stock.picking';
                                        param_write.kwargs = {};
                                        param_write.kwargs.context=this.context;
                                        var prom = this.call('ajax', 'rpc', "/web/dataset/call_kw/stock.picking/write", JSON.parse(JSON.stringify(param_write)), null, this);
                                        $(".o_barcode_summary_location_dest ").text(product.x_location[1]);    
                                    }
                                }
                            }
                        }
                        //--------------------------------------------------------------
                        
                        linesActions.push([this.linesWidget.addProduct, [res.lineDescription, this.actionParams.model]]);
                    }
                } else {
                     //--------------------------------------------------------------
                    if (self.currentState.location_dest_id != undefined && product.x_location != undefined && self.currentState.picking_type_code == "internal" && self.currentState.location_dest_id.id != product.x_location[0])
                    {
                        errorMessage = 'El producto seleccionado se encuentra en la ubicación ' + product.x_location[1] + ', esta ubicacion es distinta a ' + self.currentState.location_dest_id.display_name;
                        return Promise.reject(errorMessage);
                    }
                    //--------------------------------------------------------------
                    
                    if (product.tracking === 'none' || !self.requireLotNumber) {
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
        // _step_product: function (barcode, linesActions) {
        //     // if (barcode == "123")
        //     //barcode = "3057067316251";
        //     //barcode = "3057067316251";
        //     // if (barcode != "845973020071")
        //     // {
        //     //     console.log("es vacio");
        //     //     barcode = "3057067316251";
        //     // }
        //     if (this.scannedLines == ""){
        //         barcode = "3057067316251";
        //     }
        //     else
        //         barcode = "3057067316255";
        //     console.log(barcode);
        //     var self = this;
        //     this.currentStep = 'product';
        //     var errorMessage;
    
        //     var product = this._isProduct(barcode);
        //     console.log("product");
        //     console.log(product);
        //     if (product) {
        //         if (product.tracking !== 'none') {
        //             this.currentStep = 'lot';
        //         }
        //         var res = this._incrementLines({'product': product, 'barcode': barcode});
        //         console.log(res);
        //         if (res.isNewLine) {
        //             if (this.actionParams.model === 'stock.inventory') {
        //                 // FIXME sle: add owner_id, prod_lot_id, owner_id, product_uom_id
        //                 return this._rpc({
        //                     model: 'product.product',
        //                     method: 'get_theoretical_quantity',
        //                     args: [
        //                         res.lineDescription.product_id.id,
        //                         res.lineDescription.location_id.id,
        //                     ],
        //                 }).then(function (theoretical_qty) {
        //                     res.lineDescription.theoretical_qty = theoretical_qty;
        //                     linesActions.push([self.linesWidget.addProduct, [res.lineDescription, self.actionParams.model]]);
        //                     self.scannedLines.push(res.id || res.virtualId);
        //                     return Promise.resolve({linesActions: linesActions});
        //                 });
        //             } else {
        //                 if (self.currentState.location_dest_id != undefined && product.x_location != undefined && self.currentState.picking_type_code == "internal" && self.currentState.location_dest_id.id != product.x_location[0])
        //                 {
        //                     if (self.scannedLines != "")
        //                     {
        //                         var index = this._getLines(this.currentState).indexOf(res.lineDescription);
        //                         if (index !== -1) {
        //                             this._getLines(this.currentState).splice(index, 1);
        //                         }
        //                         var index = this.pages[this.currentPageIndex].lines.indexOf(res.lineDescription);
        //                         if (index !== -1) {
        //                             this.pages[this.currentPageIndex].lines.splice(index, 1);
        //                         }
        //                         //this._getLines(this.currentState).push(line);
        //                         //this.pages[this.currentPageIndex].lines.push(line);
        //                         errorMessage = 'El producto seleccionado se encuentra en la ubicación ' + product.x_location[1] + ', esta ubicacion es distinta a ' + self.currentState.location_dest_id.display_name;
        //                         return Promise.reject(errorMessage);    
        //                     }
        //                     else
        //                     {
        //                         res.lineDescription['location_dest_id'] = {
        //                             'id': product.x_location[0],
        //                             'display_name': product.x_location[1],
        //                         };
        //                         res.lineDescription['result_package_id'] = [product.x_package[0], product.x_package[1]];

        //                         if (product.x_location_barcode)
        //                         {
        //                             var destinationLocation = self.locationsByBarcode[product.x_location_barcode];
        //                             if (destinationLocation) {
        //                                 //self.pages[0].location_dest_id = location_dest_id
        //                                 // var currentPage = this.pages[0];
        //                                 // currentPage.location_dest_id = destinationLocation.id
        //                                 // this.currentState.location_dest_id = destinationLocation;
        //                                 self.currentState.location_dest_id = destinationLocation;

        //                                 //self.set_location_dest_barcode = product.x_location_barcode;
        //                                 var param_write = {};
        //                                 param_write.args = [[self.currentState.id], {location_dest_id: destinationLocation.id}];
        //                                 param_write.method = 'write';
        //                                 param_write.model='stock.picking';
        //                                 param_write.kwargs = {};
        //                                 param_write.kwargs.context=this.context;
        //                                 var prom = this.call('ajax', 'rpc', "/web/dataset/call_kw/stock.picking/write", JSON.parse(JSON.stringify(param_write)), null, this);
        //                                 $(".o_barcode_summary_location_dest ").text(product.x_location[1]);    
        //                             }
        //                         }
        //                     }
        //                 }
        //                 //--------------------------------------------------------------

        //                 linesActions.push([this.linesWidget.addProduct, [res.lineDescription, this.actionParams.model]]);
        //             }
        //         } else {
        //             //--------------------------------------------------------------
        //             if (self.currentState.location_dest_id != undefined && product.x_location != undefined && self.currentState.picking_type_code == "internal" && self.currentState.location_dest_id.id != product.x_location[0])
        //             {
        //                 errorMessage = 'El producto seleccionado se encuentra en la ubicación ' + product.x_location[1] + ', esta ubicacion es distinta a ' + self.currentState.location_dest_id.display_name;
        //                 return Promise.reject(errorMessage);
        //             }
        //             //--------------------------------------------------------------
        //             if (product.tracking === 'none') {
        //                 linesActions.push([this.linesWidget.incrementProduct, [res.id || res.virtualId, product.qty || 1, this.actionParams.model]]);
        //             } else {
        //                 linesActions.push([this.linesWidget.incrementProduct, [res.id || res.virtualId, 0, this.actionParams.model]]);
        //             }
        //         }
        //         this.scannedLines.push(res.id || res.virtualId);
        //         return Promise.resolve({linesActions: linesActions});
        //     } else {
        //         var success = function (res) {
        //             return Promise.resolve({linesActions: res.linesActions});
        //         };
        //         var fail = function (specializedErrorMessage) {
        //             self.currentStep = 'product';
        //             if (specializedErrorMessage){
        //                 return Promise.reject(specializedErrorMessage);
        //             }
        //             if (! self.scannedLines.length) {
        //                 if (self.groups.group_tracking_lot) {
        //                     errorMessage = _t("You are expected to scan one or more products or a package available at the picking's location");
        //                 } else {
        //                     errorMessage = _t('You are expected to scan one or more products.');
        //                 }
        //                 return Promise.reject(errorMessage);
        //             }
    
        //             var destinationLocation = self.locationsByBarcode[barcode];
        //             if (destinationLocation) {
        //                 return self._step_destination(barcode, linesActions);
        //             } else {
        //                 errorMessage = _t('You are expected to scan more products or a destination location.');
        //                 return Promise.reject(errorMessage);
        //             }
        //         };
        //         return self._step_lot(barcode, linesActions).then(success, function () {
        //             return self._step_package(barcode, linesActions).then(success, fail);
        //         });
        //     }
        // },
    });
    return StockBarcodeClientAction;
});