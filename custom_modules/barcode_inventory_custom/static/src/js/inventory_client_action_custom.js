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
    });
    return InventoryClientAction;
});