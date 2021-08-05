odoo.define('package_barcode_so_custom.SettingsWidgetCustom', function (require) {
'use strict';

var SettingsWidget = require('stock_barcode.SettingsWidget');
var core = require('web.core');
var _t = core._t;

SettingsWidget.include({
    events: _.extend(SettingsWidget.prototype.events, {
        "click .o_print_bultos_pdf": "onClickBultosPDF",
    }),
    onClickBultosPDF: function (ev) {
        ev.stopPropagation();
        this.trigger_up('picking_print_bultos_pdf');
    },
    init: function() {
        return this._super.apply(this, arguments);
    },
});
});
