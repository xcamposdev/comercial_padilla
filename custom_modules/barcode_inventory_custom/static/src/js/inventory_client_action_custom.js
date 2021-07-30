odoo.define('barcode_inventory_custom.inventory_client_action_custom', function (require) {
    "use strict";

    var InventoryClientAction = require("stock_barcode.inventory_client_action");
    var core = require('web.core');
    var _t = core._t;

    InventoryClientAction.include({
        isChildOf(locationParent, locationChild) {
            return _.str.startsWith(locationChild.parent_path, locationParent.parent_path);
        },
        _change_source: async function(new_location) {
            var self = this;
            const response = await self._rpc({
                    model: 'stock.inventory',
                    method: 'change_source',
                    args: [self.currentState.id, new_location],
                });
            return response;
        },
        _step_source: function (barcode, linesActions) {
            var self = this;
            this.currentStep = 'source';
            var errorMessage;

            /* Bypass this step in the following cases:
               - the picking is a receipt
               - the multi location group isn't active
            */
            var sourceLocation = this.locationsByBarcode[barcode];
            const locationId = this._getLocationId();
            if (sourceLocation  && ! (this.mode === 'receipt' || this.mode === 'no_multi_locations')) {
                // There's nothing to do on the state here, just mark `this.scanned_location`.
                if (locationId && !this.isChildOf(locationId, sourceLocation)) {
                    self._change_source(sourceLocation).then(function(res) {
                        linesActions.push([self.linesWidget.highlightLocation, [true]]);
                        self.scanned_location = sourceLocation;
                        self.currentStep = 'product';
                        return Promise.resolve({linesActions: linesActions});
                    });
                }
                linesActions.push([this.linesWidget.highlightLocation, [true]]);
                if (this.actionParams.model === 'stock.picking') {
                    linesActions.push([this.linesWidget.highlightDestinationLocation, [false]]);
                }
                this.scanned_location = sourceLocation;
                this.currentStep = 'product';
                return Promise.resolve({linesActions: linesActions});
            }
            /* Implicitely set the location source in the following cases:
                - the user explicitely scans a product
                - the user explicitely scans a lot
                - the user explicitely scans a package
            */
            // We already set the scanned_location even if we're not sure the
            // following steps will succeed. They need scanned_location to work.
            this.scanned_location = {
                id: this.pages ? this.pages[this.currentPageIndex].location_id : this.currentState.location_id.id,
                display_name: this.pages ? this.pages[this.currentPageIndex].location_name : this.currentState.location_id.display_name,
            };
            linesActions.push([this.linesWidget.highlightLocation, [true]]);
            if (this.actionParams.model === 'stock.picking') {
                linesActions.push([this.linesWidget.highlightDestinationLocation, [false]]);
            }

            return this._step_product(barcode, linesActions).then(function (res) {
                return Promise.resolve({linesActions: res.linesActions});
            }, function (specializedErrorMessage) {
                delete self.scanned_location;
                self.currentStep = 'source';
                if (specializedErrorMessage){
                    return Promise.reject(specializedErrorMessage);
                }
                var errorMessage = _t('You are expected to scan a source location.');
                return Promise.reject(errorMessage);
            });
        },
        _findCandidateLineToIncrement: function (params) {
            var product = params.product;
            var lotId = params.lot_id;
            var lotName = params.lot_name;
            var packageId = params.package_id;
            var currentPage = this.pages[this.currentPageIndex];
            var res = false;
            for (var z = 0; z < currentPage.lines.length; z++) {
                var lineInCurrentPage = currentPage.lines[z];
                if (lineInCurrentPage.product_id.id === product.id &&
                    (product.x_package == undefined && lineInCurrentPage.package_id == undefined
                    || (product.x_package != undefined && lineInCurrentPage.package_id != undefined && product.x_package[0] == lineInCurrentPage.package_id[0]))
                    ) {
                    // If the line is empty, we could re-use it.
                    if (lineInCurrentPage.virtual_id &&
                        (this.actionParams.model === 'stock.picking' &&
                         ! lineInCurrentPage.qty_done &&
                         ! lineInCurrentPage.product_uom_qty &&
                         ! lineInCurrentPage.lot_id &&
                         ! lineInCurrentPage.lot_name &&
                         ! lineInCurrentPage.package_id
                        ) ||
                        (this.actionParams.model === 'stock.inventory' &&
                         ! lineInCurrentPage.product_qty &&
                         ! lineInCurrentPage.prod_lot_id
                        )
                    ) {
                        res = lineInCurrentPage;
                        break;
                    }

                    if (product.tracking === 'serial' &&
                        ((this.actionParams.model === 'stock.picking' &&
                          lineInCurrentPage.qty_done > 0
                         ) ||
                        (this.actionParams.model === 'stock.inventory' &&
                         lineInCurrentPage.product_qty > 0
                        ))) {
                        continue;
                    }
                    if (lineInCurrentPage.qty_done &&
                    (this.actionParams.model === 'stock.inventory' ||
                    lineInCurrentPage.location_dest_id.id === currentPage.location_dest_id) &&
                    this.scannedLines.indexOf(lineInCurrentPage.virtual_id || lineInCurrentPage.id) === -1 &&
                    lineInCurrentPage.qty_done >= lineInCurrentPage.product_uom_qty) {
                        continue;
                    }
                    if (lotId &&
                        ((this.actionParams.model === 'stock.picking' &&
                         lineInCurrentPage.lot_id &&
                         lineInCurrentPage.lot_id[0] !== lotId
                         ) ||
                        (this.actionParams.model === 'stock.inventory' &&
                         lineInCurrentPage.prod_lot_id &&
                         lineInCurrentPage.prod_lot_id[0] !== lotId
                        )
                    )) {
                        continue;
                    }
                    if (lotName &&
                        lineInCurrentPage.lot_name &&
                        lineInCurrentPage.lot_name !== lotName
                        ) {
                        continue;
                    }
                    if (packageId &&
                        (! lineInCurrentPage.package_id ||
                        lineInCurrentPage.package_id[0] !== packageId[0])
                        ) {
                        continue;
                    }
                    if(lineInCurrentPage.product_uom_qty && lineInCurrentPage.qty_done >= lineInCurrentPage.product_uom_qty) {
                        continue;
                    }
                    res = lineInCurrentPage;
                    break;
                }
            }
            return res;
        },
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
                            if (product.x_package != undefined) {
                                res.lineDescription['result_package_id'] = [product.x_package[0], product.x_package[1]];
                                res.lineDescription['package_id'] = [product.x_package[0], product.x_package[1]];
                                console.log(res);
                            }
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
                                        self.currentState.location_dest_id = destinationLocation;
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
                    if (!self.has_origin && self.currentState.location_dest_id != undefined && product.x_location != undefined && self.currentState.picking_type_code == "internal" && self.currentState.location_dest_id.id != product.x_location[0])
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
    });
    return InventoryClientAction;
});
