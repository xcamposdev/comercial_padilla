odoo.define('stock_barcode_custom.SaleMenu', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var QWeb = core.qweb;
var Dialog = require('web.Dialog');
var Session = require('web.session');

var _t = core._t;

var SaleMenu = AbstractAction.extend({
    contentTemplate: 'sale_barcode_menu',

    events: {
        "click .button_type_pick": function(){
            this.do_action('stock_barcode_custom.sale_order_action_kanban_pick');
        },
        "click .button_type_pack": function(){
            this.do_action('stock_barcode_custom.sale_order_action_kanban_pack');
        },
        "click .button_type_out": function(){
            this.do_action('stock_barcode_custom.sale_order_action_kanban_out');
        },
    },

    init: function(parent, action) {
        console.log('sale menu');
        this._super.apply(this, arguments);
    },

    willStart: function () {
        return this._super.apply(this, arguments);
    },

    start: function() {
        this._super();
    },

    destroy: function () {
        this._super();
    },
});

core.action_registry.add('stock_barcode_sale_menu', SaleMenu);

return {
    SaleMenu: SaleMenu,
};

});
