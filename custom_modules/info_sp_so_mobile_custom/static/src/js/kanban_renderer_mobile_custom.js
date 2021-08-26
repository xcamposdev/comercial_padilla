odoo.define('info_sp_so_mobile_custom.kanban_renderer_mobile_custom_js', function (require) {
    "use strict";
    
    var KanbanController = require('web.KanbanController');
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');


    KanbanController.include({
        _onLoadColumnRecords: function (ev) {
            var self = this;
            this.model.loadColumnRecords(ev.data.columnID).then(function (dbID) {
                var data = self.model.get(dbID);
                return self.renderer.updateColumn(dbID, data).then(function() {
                    self._updateEnv();
                    if (ev.data.onSuccess) {
                        ev.data.onSuccess();
                    }
                    self.loadOriginSale(dbID, data);
                });
            });
        },
        loadOriginSale: function (dbID, data) {
            if (data != null && data.domain.length > 0)// && data.domain[0].length == 3 && data.domain[0][0] == "origin")
            {
                for (let i = 0; i < data.domain.length; i++)
                {
                    if (data.domain[i].length == 3 && data.domain[i][0] == "origin")
                    {
                        ajax.jsonRpc('/web/dataset/call_kw', 'call', {
                            'model': 'stock.picking',
                            'method': 'get_origin_sale_kanban',
                            'args': [[],data.domain[i][2]],
                            'kwargs': {
                                'context': {},
                            }
                        }).then(function (data) {
                            if (data != false)
                            {
                                var div_content = $(".o_kanban_group.o_current").find("div[data-id='" + dbID + "']");
                                var content = "<div class='oe_kanban_card o_kanban_record oe_kanban_card_muted'>";
                                content += "<div><strong>Cliente: </strong>" + data['partner_name'] + "</div>";
                                if (data['is_tss'] == true) 
                                    content += "<div><strong>TSS: </strong>TSS</div>";
                                else
                                    content += "<div><strong>TSS: </strong>Comercial Padilla</div>";
                                content += "<div><strong>Peso: </strong>" + data['weight'] + "</div>";
                                content += "<div><strong>Número de lineas de la venta: </strong>" + data['number_of_lines'] + "</div>";
                                content += "</div>"
                                div_content.prevObject.prepend(content);
                            }
                        });
                    }
                }
            }
        }
    });

    return KanbanController;
});