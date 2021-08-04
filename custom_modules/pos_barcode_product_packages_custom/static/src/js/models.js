odoo.define('pos_barcode_product_packages_custom.load_product_models', function (require) {
"use strict";
	var models = require('point_of_sale.models');

	models.PosModel.prototype.models.push({
        model:  'product.packaging',
        domain: function(self){
            var domain = [['barcode', '!=', false],['product_id.available_in_pos','=',true],'|',['product_id.company_id','=',self.config.company_id[0]],['product_id.company_id','=',false]];
            return domain;
        },
        loaded: function(self, prod_packages){
           self.prod_packages = prod_packages;
           for (var key in prod_packages) {
                self.packages_barcodes[prod_packages[key]['barcode']] = prod_packages[key];
           }
        },
    });

    var _super_pos_model = models.PosModel.prototype;
    
    models.PosModel = models.PosModel.extend({
        initialize: function(session, attributes){
            _super_pos_model.initialize.call(this, session, attributes);
            this.prod_packages = [];
            this.packages_barcodes = {};
        },
        scan_product: function(parsed_code){
            var selectedOrder = this.get_order();
            var res_scan = _super_pos_model.scan_product.call(this, parsed_code);
            if (!res_scan && this.packages_barcodes[parsed_code.base_code] !== undefined) {
                var prod_package = this.packages_barcodes[parsed_code.base_code];
                var product = this.db.get_product_by_id(prod_package.product_id[0]);
                product['package_id'] = prod_package.id;
                selectedOrder.add_product(product, {quantity:prod_package.qty, package_id: prod_package.id, merge:true});
                return true;
            }
            return res_scan;
        },
    });
});