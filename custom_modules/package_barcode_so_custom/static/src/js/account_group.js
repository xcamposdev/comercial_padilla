odoo.define('account_message_custom.account_message_javascript', function (require) {
    'use strict';

    //var models = require('account_move.models')

    

    // var Widget = require('web.Widget');
    // var MyWidget = Widget.extend({
    //     start: function () {
    //         alert("test");
    //         // this.counter = new Counter(this);
    //         // this.counter.on('valuechange', this, this._onValueChange);
    //         // var def = this.counter.appendTo(this.$el);
    //         // return $.when(def, this._super.apply(this, arguments);
    //     },
    //     _onValueChange: function (val) {
    //         // do something with val
    //     },
    // });
    
    // in Counter widget, we need to call the trigger method:
    
    //this.trigger('valuechange', someValue);

    //var ViewRegistry = require('web.view_registry');
    //viewRegistry.add('map', MapView);
    
    // this.do_warn(_t("Error"), _t("Filter name is required."));

    // note that we call _t on the text to make sure it is properly translated.
    //this.do_notify(_t("Success"), _t("Your signature request has been sent."));
    //this.do_warn(_t("Error"), _t("Filter name is required."));

   

    // ViewRegistry.include({
    //     load_views: function (load_fields) {
    //         // var self = this;
    //         alert("DIO");
    //         // // Check if left menu visible
    //         // var root=self.$el.parents();
    //         // var visible=(root.find('.o_sub_menu').css('display') != 'none')
    //         // if (visible) {
    //         //     // Show menu and resize form components to original values
    //         //     root.find('.o_form_sheet_bg').css('padding', self.sheetbg_padding);
    //         //     root.find('.o_form_sheet').css('max-width', self.sheetbg_maxwidth);
    //         //     root.find('.o_form_view div.oe_chatter').css('max-width', self.chatter_maxwidth);
    //         // } else {
    //         //     // Hide menu and save original values
    //         //     self.sheetbg_padding=root.find('.o_form_sheet_bg').css('padding');
    //         //     root.find('.o_form_sheet_bg').css('padding', '16px');
    //         //     self.sheetbg_maxwidth=root.find('.o_form_sheet').css('max-width');
    //         //     root.find('.o_form_sheet').css('max-width', '100%');
    //         //     self.chatter_maxwidth=root.find('.o_form_view div.oe_chatter').css('max-width');
    //         //     root.find('.o_form_view div.oe_chatter').css('max-width','100%');
    //         // }

    //         // return this._super.apply(this, arguments, load_fields);
    //     },
    // });
});

// You can use do_warn or do_notify function to create notification on top-right Odoo screen.
// this.do_warn(title, message, sticky, className);
// Same params for do_notify.

// If you want display warning in popup(dialog) then you can use alert dialog.
// var Dialog = require('web.Dialog');
// Dialog.alert(this, message, options);