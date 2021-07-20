odoo.define('stock_move_barcode_track.SettingsWidgetCustom', function (require) {
'use strict';

var SettingsWidget = require('stock_barcode.SettingsWidget');
var core = require('web.core');
var _t = core._t;

SettingsWidget.include({
    events: _.extend(SettingsWidget.prototype.events, {
        "click .o_print_matricula_pdf": "onClickMatriculaPDF",
    }),
     onClickMatriculaPDF: function (ev) {
        ev.stopPropagation();
        this.trigger_up('picking_print_matricula_pdf');
    },
    init: function() {
        return this._super.apply(this, arguments);
    },
});
});
