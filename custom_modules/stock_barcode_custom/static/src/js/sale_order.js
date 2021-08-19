odoo.define('stock_barcode_custom.sale_order_kanban', function (require) {
    'use strict';
    
    var KanbanRecord = require('web.KanbanRecord');
    
    KanbanRecord.include({
        //--------------------------------------------------------------------------
        // Private
        //--------------------------------------------------------------------------
    
        /**
         * @override
         * @private
         */
        _openRecord: function () {
            if (this.modelName === 'sale.order' && this.$('button').length) {
                this.$('button').first().click();
            } else {
                this._super.apply(this, arguments);
            }
        }
    });
    
});
    