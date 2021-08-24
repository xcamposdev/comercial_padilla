odoo.define('stock_barcode_custom.inventory_client_action', function (require) {
'use strict';

var core = require('web.core');
var ClientAction = require('stock_barcode_custom.ClientAction');
var ViewsWidget = require('stock_barcode_custom.ViewsWidget');

var _t = core._t;

var InventoryClientAction = ClientAction.extend({
    custom_events: _.extend({}, ClientAction.prototype.custom_events, {
        validate: '_onValidate',
        cancel: '_onCancel',
        show_information: '_onShowInformation',
        picking_print_inventory: '_onPrintInventory'
    }),

    init: function (parent, action) {
        this._super.apply(this, arguments);
        this.commands['O-BTN.validate'] = this._validate.bind(this);
        this.commands['O-BTN.cancel'] = this._cancel.bind(this);
        this.mode = 'inventory';
        if (! this.actionParams.inventoryId) {
            this.actionParams.inventoryId = action.context.active_id;
            this.actionParams.model = 'stock.inventory';
        }
    },

    willStart: function () {
        var self = this;
        var res = this._super.apply(this, arguments);
        res.then(function () {
            if (self.currentState.group_stock_multi_locations === false) {
                self.mode = 'no_multi_locations';
            } else  {
                self.mode = 'inventory';
            }
            if (self.currentState.state === 'done') {
                self.mode = 'done';
            }
        });
        return res;
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * @override
     */
    _getWriteableFields: function () {
        return ['product_qty', 'location_id.id', 'prod_lot_id.id'];
    },


    /**
     * @override
     */
     _getPageFields: function (options) {
         if (options && options.line) {
            return [
                ['location_id', 'location_id.id'],
                ['location_name', 'location_id.display_name'],
            ];
         }
         return [
             ['location_id', 'location_ids.0.id'],
             ['location_name', 'location_ids.0.display_name'],
         ];
     },

    /**
     * @override
     */
    _getLines: function (state) {
        return state.line_ids;
    },

    /**
     * @override
     */
    _lot_name_used: function (product, lot_name) {
        var lines = this._getLines(this.currentState);
        for (var i = 0; i < lines.length; i++) {
            var line = lines[i];
            if (line.product_qty !== 0 && line.product_id.id === product.id &&
                line.prod_lot_id && line.prod_lot_id[1] === lot_name) {
                return true;
            }
        }
        return false;
    },

    /**
     * @override
     */
    _makeNewLine: function (product, barcode, qty_done, package_id) {
        var virtualId = this._getNewVirtualId();
        var currentPage = this.pages[this.currentPageIndex];
        var newLine = {
            'inventory_id': this.currentState.id,
            'product_id': {
                'id': product.id,
                'display_name': product.display_name,
                'barcode': barcode,
                'tracking': product.tracking,
            },
            'product_barcode': barcode,
            'display_name': product.display_name,
            'product_qty': qty_done,
            'theoretical_qty': 0,
            'product_uom_id': product.uom_id[0],
            'location_id': {
                'id': currentPage.location_id,
                'name': currentPage.location_name,
            },
            'package_id': package_id,
            'state': 'confirm',
            'reference': this.name,
            'virtual_id': virtualId,
        };
        return newLine;
    },

    /**
     * @override
     */
    _applyChanges: function (changes) {
        var formattedCommands = [];
        var cmd = [];
        for (var i in changes) {
            var line = changes[i];

            // Lines needs to be updated
            if (line.id) {
                cmd = [1, line.id, {
                    'product_qty' : line.product_qty,
                    'prod_lot_id': line.prod_lot_id && line.prod_lot_id[0],
                    'package_id': line.package_id && line.package_id[0],
                }];
                formattedCommands.push(cmd);
            // Lines needs to be created
            } else {
                cmd = [0, 0, {
                    'product_id':  line.product_id.id,
                    'product_uom_id': line.product_uom_id,
                    'product_qty': line.product_qty,
                    'location_id': line.location_id.id,
                    'prod_lot_id': line.prod_lot_id && line.prod_lot_id[0],
                    'package_id': line.package_id && line.package_id[0],
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
                'write_field': 'line_ids',
            };

            return this._rpc({
                'route': '/stock_barcode_custom/get_set_barcode_view_state',
                'params': params,
            });
        } else {
            return Promise.reject();
        }
    },

    /**
     * @override
     */
    _showInformation: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            if (self.ViewsWidget) {
                self.ViewsWidget.destroy();
            }
            self.linesWidget.destroy();
            self.ViewsWidget = new ViewsWidget(
                self,
                'stock.inventory',
                'stock_barcode_custom.stock_inventory_barcode2',
                {},
                {currentId :self.currentState.id},
                'readonly'
            );
            self.ViewsWidget.appendTo(self.$('.o_content'));
        });
    },

    /**
     * Makes the rpc to `action_validate`.
     * This method could open a wizard so it takes care of removing/adding the "barcode_scanned"
     * event listener.
     *
     * @private
     * @returns {Promise}
     */
     _validate: function (ev) {
        var self = this;
        this.mutex.exec(function () {
            return self._save().then(function () {
                self._rpc({
                    'model': self.actionParams.model,
                    'method': 'action_validate',
                    'args': [[self.currentState.id]],
                }).then(function () {
                    self.do_notify(_t("Success"), _t("The inventory adjustment has been validated"));
                    return self.trigger_up('exit');
                });
            });
        });
    },

    /**
     * Makes the rpc to `action_cancel`.
     *
     * @private
     */
    _cancel: function () {
        var self = this;
        this.mutex.exec(function () {
            return self._save().then(function () {
                return self._rpc({
                    'model': self.actionParams.model,
                    'method': 'action_cancel_draft',
                    'args': [[self.currentState.id]],
                }).then(function () {
                    self.do_notify(_t("Cancel"), _t("The inventory adjustment has been cancelled"));
                    self.trigger_up('exit');
                });
            });
        });
    },

    //--------------------------------------------------------------------------
    // Handlers
    //--------------------------------------------------------------------------

    /**
     * Handles the `validate` OdooEvent.
     *
     * @private
     * @param {OdooEvent} ev
     */
     _onValidate: function (ev) {
         ev.stopPropagation();
         this._validate();
     },

    /**
    * Handles the `cancel` OdooEvent.
    *
    * @private
    * @param {OdooEvent} ev
    */
    _onCancel: function (ev) {
        ev.stopPropagation();
        this._cancel();
    },

    /**
     * Handles the `print_inventory` OdooEvent. It makes an RPC call
     * to the method 'do_action' on a 'ir.action_window' with the additional context
     * needed
     *
     * @private
     * @param {OdooEvent} ev
     */
    _onPrintInventory: function (ev) {
        ev.stopPropagation();
        var self = this;
        this.mutex.exec(function () {
            return self._save().then(function () {
                return self.do_action(self.currentState.actionReportInventory, {
                    'additional_context': {
                        'active_id': self.actionParams.id,
                        'active_ids': [self.actionParams.inventoryId],
                        'active_model': 'stock.inventory',
                    }
                });
            });
        });
    },

    /*\ - Barcode Inventary custom - /*/
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
                    if (!res) {
                        errorMessage = _t("Unable to change source destination please check contact with the administrator.");
                        return Promise.reject(errorMessage);
                    }
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
                            if (product.x_package == false) {
                                errorMessage = 'El Producto seleccionado no cuenta con un empaquetado assignado.';
                                return Promise.reject(errorMessage);
                            }
                            res.lineDescription['result_package_id'] = [product.x_package[0], product.x_package[1]];
                            res.lineDescription['package_id'] = [product.x_package[0], product.x_package[1]];
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

core.action_registry.add('stock_barcode_inventory_client_action', InventoryClientAction);

return InventoryClientAction;

});
