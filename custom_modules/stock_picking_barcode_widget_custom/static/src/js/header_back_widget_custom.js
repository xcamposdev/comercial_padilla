odoo.define('stock_picking_barcode_widget.header_back_widget_custom_js', function (require) {
    "use strict";
    var Widget = require('stock_barcode.HeaderWidget');
    var BackWidget = Widget;

    BackWidget.include({
        _onClickExit: function (ev) {
            ev.stopPropagation();
            console.log('back to list');
            var self = this;
            var code = localStorage.getItem('selected_barcode');
            if(code != null) {
                localStorage.setItem('selected_barcode', code)
            }
            self.trigger_up('exit')
        }
    });    
});