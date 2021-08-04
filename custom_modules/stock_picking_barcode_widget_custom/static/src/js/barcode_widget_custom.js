odoo.define('stock_picking_barcode_widget.barcode_widget_custom_js', function (require) {
   "use strict";
    var KanbanRenderer = require('web.KanbanRenderer');

    KanbanRenderer.include({
        _onMobileTabClicked: function (event) {
            if(this._canCreateColumn() && !this.quickCreate.folded) {
                this.quickCreate.toggleFold();
            }
            var column = this.widgets[$(event.currentTarget).index()];
            var columnID = column.id || column.db_id;
            localStorage.setItem('selected_barcode', columnID)
            localStorage.setItem('selected_index', $(event.currentTarget).index())
            this._moveToGroup($(event.currentTarget).index(), true);
        },
     
        _computeCurrentColumn: function () {
            if (this.widgets.length) {
                var activeColumnIndex = localStorage.getItem('selected_index');
                this.activeColumnIndex = activeColumnIndex ? activeColumnIndex : this.activeColumnIndex;
                var column = this.widgets[this.activeColumnIndex];
                if (!column) {
                    return;
                }
                var columnID = localStorage.getItem('selected_barcode') ? localStorage.getItem('selected_barcode') : column.id || column.db_id;
                
                this.$('.o_kanban_mobile_tab.o_current, .o_kanban_group.o_current')
                    .removeClass('o_current');
                this.$('.o_kanban_group[data-id="' + columnID + '"], ' +
                       '.o_kanban_mobile_tab[data-id="' + columnID + '"]')
                    .addClass('o_current');
            }
        },
    });
});