odoo.define('product_packaging_custom.picking_client_action_custom_js', function (require) {
    "use strict";
    
    var PickingClientAction = require("stock_barcode.picking_client_action");
    var core = require('web.core');
    var _t = core._t;

    
    PickingClientAction.include({
        willStart: function () {
            var self = this;
            var res = this._super.apply(this, arguments);
            var prom = self._has_origin_picking(this.actionParams.pickingId);
            prom.then(function(has_origin){
                res.then(function() {
                    // Get the usage of the picking type of `this.picking_id` to chose the mode between
                    // `receipt`, `internal`, `delivery`.
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
            const response = await this._rpc({
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
                'package_size': package_id !== undefined || package_id !== null ? qty_done : false,
                'packages_count': package_id !== undefined || package_id !== null ? 1 : false,
            };
            return newLine;
        },
        _incrementLines: function (params) {
            var line = this._findCandidateLineToIncrement(params);
            var isNewLine = false;

            if (line) {
                // Update the line with the processed quantity.
                if (params.product.tracking === 'none' ||
                    params.lot_id ||
                    params.lot_name
                    ) {
                    if (this.actionParams.model === 'stock.picking') {
                        line.qty_done += params.product.qty || 1;

                        if (line.package_size) {
                            line.packages_count = line.qty_done/line.package_size;
                            var $line = this.$("[data-id='" + line.virtual_id + "']");
                            var incrementClass = '.packages_count';

                            $line.find(incrementClass).text(line.packages_count);
                        }
                        if (params.package_id) {
                            line.package_id = params.package_id;
                        }
                        if (params.result_package_id) {
                            line.result_package_id = params.result_package_id;
                        }
                    } else if (this.actionParams.model === 'stock.inventory') {
                        line.product_qty += params.product.qty || 1;
                    }
                }
            } else {
                isNewLine = true;
                // Create a line with the processed quantity.
                if (params.product.tracking === 'none' ||
                    params.lot_id ||
                    params.lot_name
                    ) {
                    line = this._makeNewLine(params.product, params.barcode, params.product.qty || 1, params.package_id, params.result_package_id, params.owner_id);
                } else {
                    line = this._makeNewLine(params.product, params.barcode, 0, params.package_id, params.result_package_id);
                }
                this._getLines(this.currentState).push(line);
                this.pages[this.currentPageIndex].lines.push(line);
            }
            if (this.actionParams.model === 'stock.picking') {
                if (params.lot_id) {
                    line.lot_id = [params.lot_id];
                }
                if (params.lot_name) {
                    line.lot_name = params.lot_name;
                }
            } else if (this.actionParams.model === 'stock.inventory') {
                if (params.lot_id) {
                    line.prod_lot_id = [params.lot_id, params.lot_name];
                }
            }
            return {
                'id': line.id,
                'virtualId': line.virtual_id,
                'lineDescription': line,
                'isNewLine': isNewLine,
            };
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
                            res.lineDescription['result_package_id'] = [product.x_package[0], product.x_package[1]];
                            res.lineDescription['package_id'] = [product.x_package[0], product.x_package[1]];
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
    return PickingClientAction;
});
