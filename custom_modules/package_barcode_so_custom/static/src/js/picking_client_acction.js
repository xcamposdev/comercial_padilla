odoo.define('package_barcode_so_custom.PickingClientActionCustom', function (require) {
'use strict';

var core = require('web.core');
var PickingClientActionCustom = require('stock_barcode.picking_client_action');
var _t = core._t;

PickingClientActionCustom.include({
    custom_events: _.extend(PickingClientActionCustom.prototype.custom_events, {
        "picking_print_bultos_pdf": "_onPrintBultosPdf",
    }),
    _onPrintBultosPdf: function (ev) {
        ev.stopPropagation();
        this._printBultosPdf();
    },
     _printBultosPdf: function () {
        var self = this;
        this.mutex.exec(function () {
            return self._save().then(function () {
                console.log(self)
                return self.do_action(self.currentState.actionReportBultoId, {
                    'additional_context': {
                        'active_id': self.actionParams.pickingId,
                        'active_ids': [self.actionParams.pickingId],
                        'active_model': 'stock.picking',
                    }
                });
            });
        });
    },
});
});
