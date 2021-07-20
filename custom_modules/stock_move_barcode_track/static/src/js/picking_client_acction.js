odoo.define('stock_move_barcode_track.PickingClientActionCustom', function (require) {
'use strict';

var core = require('web.core');
var PickingClientActionCustom = require('stock_barcode.picking_client_action');
var _t = core._t;

PickingClientActionCustom.include({
    custom_events: _.extend(PickingClientActionCustom.prototype.custom_events, {
        "picking_print_matricula_pdf": "_onPrintMatriculaPdf",
    }),
    _onPrintMatriculaPdf: function (ev) {
        ev.stopPropagation();
        this._printMatriculaPdf();
    },
     _printMatriculaPdf: function () {
        var self = this;
        this.mutex.exec(function () {
            return self._save().then(function () {
                return self.do_action(self.currentState.actionReportMatriculaId, {
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
