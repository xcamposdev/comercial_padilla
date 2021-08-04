odoo.define('stock_picking_barcode_widget.barcode_widget_custom_js', function (require) {
   "use strict";
    var KanbanRenderer = require('web.KanbanRenderer');

    KanbanRenderer.include({
     
        _computeCurrentColumn: function () {
            console.log('aqui')

            if (this.widgets.length) {
                var column = this.widgets[this.activeColumnIndex];
                if (!column) {
                    return;
                }
                console.log(column)
                var columnID = column.id || column.db_id;
                var title = column.title;  
                var column_code = localStorage.getItem('selected_barcode');

                if (column_code != null && columnID != column_code){
                    columnID = column_code;
                } else {
                    localStorage.setItem('selected_barcode', columnID) 
                }

                this.$('.o_kanban_mobile_tab.o_current, .o_kanban_group.o_current')
                    .removeClass('o_current');
                this.$('.o_kanban_group[data-id="' + columnID + '"], ' +
                       '.o_kanban_mobile_tab[data-id="' + columnID + '"]')
                    .addClass('o_current');
            }
        },

    });
});