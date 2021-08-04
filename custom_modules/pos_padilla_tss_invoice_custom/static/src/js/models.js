odoo.define('pos_padilla_tss_invoice_custom.load_product_models', function (require) {
"use strict";
	var models = require('point_of_sale.models');
	var session = require('web.session');
	var core = require('web.core');

	var _t = core._t;

	models.PosModel.prototype.models.push({
        model:  'res.company',
        fields: [ 'currency_id', 'email', 'website', 'company_registry', 'vat', 'name', 'phone', 'partner_id' , 'country_id', 'state_id', 'tax_calculation_rounding_method', 'x_is_tss'],
        loaded: function(self, companies){
            const company_id = session.user_context.pos_session_company_ids[0]
            for (var key in companies) {
                if(companies[key]['id'] == company_id) {
                    self.company = companies[key];
                }
                if(companies[key]['x_is_tss']) {
                    self.company_tss = companies[key];
                }
            }
        },
    });

    var load_picture = function (self) {
        self.company_logo_tss = new Image();
        if (self.company_tss === undefined) {
            return null;
        }
        return new Promise(function (resolve, reject) {
            self.company_logo_tss.onload = function () {
                var img = self.company_logo_tss;
                var ratio = 1;
                var targetwidth = 300;
                var maxheight = 150;
                if( img.width !== targetwidth ){
                    ratio = targetwidth / img.width;
                }
                if( img.height * ratio > maxheight ){
                    ratio = maxheight / img.height;
                }
                var width  = Math.floor(img.width * ratio);
                var height = Math.floor(img.height * ratio);
                var c = document.createElement('canvas');
                c.width  = width;
                c.height = height;
                var ctx = c.getContext('2d');
                ctx.drawImage(self.company_logo_tss,0,0, width, height);

                self.company_tss_logo_base64 = c.toDataURL();
                resolve();
            };
            self.company_logo_tss.onerror = function () {
                reject();
            };
            self.company_logo_tss.crossOrigin = "anonymous";
            self.company_logo_tss.src = '/web/binary/company_logo' + '?dbname=' + session.db + '&company=' + self.company_tss.id + '&_' + Math.random();
        });
    };

    models.PosModel.prototype.models.push({
        label: 'pictures2',
        loaded: load_picture,
    });

    models.load_fields("res.partner", ["x_is_tss"]);

    var super_order = models.Order.prototype;
    models.Order = models.Order.extend({
        export_for_printing: function() {
            var receipt = super_order.export_for_printing.call(this);
            if(this.pos.company_tss != undefined && receipt['client'] != null) {
                var client = this.get('client');
                if (client.x_is_tss) {
                    var company = this.pos.company_tss;
                    receipt['company'] = {
                        email: company.email,
                        website: company.website,
                        company_registry: company.company_registry,
                        contact_address: company.partner_id[1],
                        vat: company.vat,
                        vat_label: company.country && company.country.vat_label || _t('Tax ID'),
                        name: company.name,
                        phone: company.phone,
                        logo:  this.pos.company_tss_logo_base64,
                    }
                }
            }
            return receipt;
        }
    });
});
