import json
import logging
import base64
import werkzeug

from odoo import http, api, tools
from datetime import datetime
from odoo.http import content_disposition, request, Response, Controller , route, JsonRequest
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import date_utils
from functools import wraps

from odoo.exceptions import AccessError, AccessDenied
_logger = logging.getLogger(__name__)

class ApiAccess(http.Controller):

    @http.route('/api/web/authenticate', type='json', auth='public', customresp='apiresponse')
    def authenticate(self, db, login, password):
        session = request.session.authenticate(db, login, password)
        if session:
            #session = request.env['ir.http'].session_info()
            session_sid = request.session.sid
            Response.status = "200"
            return {'code': 200, 'session_id': session_sid, 'message': 'success'}
        else:
            Response.status = "401 unauthorized"
            return {'code': 401, 'error': 'No se pudo iniciar session en odoo', 'message': 'error'}      

    @http.route('/api/web/get_session_info', type='json', auth='public', customresp='apiresponse')
    def get_session_info(self, **kw):
        request.session.check_security()
        request.uid = request.session.uid
        request.disabled_db = False
        return request.env['ir.http'].session_info()

    def user_authenticate(f):
        @wraps.wraps(f)
        def wrap(*args, **kwargs):
            request.uid = request.session.uid
            if not request.uid:
                Response.status = "401 unauthorized"            
                return {'code': 401, 'error': 'No se pudo iniciar session en odoo', 'message': 'error'} 
            return f(*args, **kwargs)
        return wrap

    @http.route('/api/web/get_products', type='json', auth='user', methods=['GET'], website=False, customresp='apiresponse')
    def get_products(self):       
        uid = request.session.uid

        if uid:
            try:
                products = []
                params = request.jsonrequest['params']

                page = 0
                limit = 1000

                if 'page' in params:
                    page = request.params['page']
                if 'limit' in params:
                    limit = request.params['limit']

                all_products = request.env['product.template'].search([('active', '=', 'true')], order='id asc', offset = page, limit = limit) 
                for p in all_products:
                    sellers = []
                    for s in p.seller_ids:
                        sellers.append(s.name.name)
                    item = {
                        'id': p.id,
                        'default_code': p.default_code,
                        'description_sale': p.description_sale,
                        'weight': p.weight,
                        'categ_id': p.categ_id.id,
                        'x_manufacturar_code': p.x_manufacturar_code if hasattr(p,'x_manufacturar_code') else '',
                        'image': p.image_1920 if p.image_1920 else '',
                        'seller_ids': ", ".join(sellers)
                    }
                    products.append(item)
                Response.status = "200"  
                return {'code': 200, 'products': products, 'message': 'success'}
            except Exception as e:
                se = _serialize_exception(e)
                error = {
                    'code': 400,
                    'message': 'Error',
                    'error': se
                }
                Response.status = "400 Bad Request"
                return error
        else:
            Response.status = "401 unauthorized"
            return {'code': 401, 'error': 'Usuario no registrado o no tiene accesso a este servicio', 'message': 'error'}

    @http.route('/api/web/get_categories', type='json', auth='user', methods=['GET'], website=False, customresp='apiresponse')
    def get_categories(self):
        uid = request.session.uid

        if uid:
            try:
                categories = []
                params = request.jsonrequest['params']

                page = 0
                limit = 1000

                if 'page' in params:
                    page = request.params['page']
                if 'limit' in params:
                    limit = request.params['limit']
                
                all_category = request.env['product.category'].with_user(request.session.uid).search([], order='id asc', offset=page, limit = limit) 

                for c in all_category:
                    item = {
                        'id': c.id,
                        'name': c.name,
                        'parent_id': c.parent_id.id
                    }
                    categories.append(item)
                Response.status = "200"    
                return {'code': 200, 'categories': categories, 'message': 'success'}
            except Exception as e:
                se = _serialize_exception(e)
                error = {
                    'code': 400,
                    'message': 'Error',
                    'error': se
                }
                Response.status = "400 Bad Request"  
                return error
        else:
            Response.status = "401 unauthorized"
            return {'code': 401, 'error': 'Usuario no registrado o no tiene accesso a este servicio', 'message': 'error'}
    
    @http.route('/api/web/get_users', type='json', auth='user', methods=['GET'], website=False, customresp='apiresponse')
    def get_users(self):
        uid = request.session.uid
        
        if uid:
            try:
                page = 0
                limit = 1000
                users = []
                params = request.jsonrequest['params']

                if 'page' in params:
                    page = request.params['page']
                if 'limit' in params:
                    limit = request.params['limit']
           
                #get users with params
                all_users = request.env['res.partner'].sudo().search([('active', '=', 'true')], order='id asc', offset=page, limit = limit) 

                for u in all_users:
                    item = {
                        'id': u.id,
                        'name': u.name,
                        'ref': u.ref,
                        'email': u.email,
                        'phone': u.phone,
                        'mobile': u.mobile,
                        'vat': u.vat
                    }
                    users.append(item)

                headers = {'Content-type': 'application/json'}
                Response.status = "200"
                data = {'code': 200, 'users': users, 'message': 'success'}   
                return data
                          
            except Exception as e:
                se = _serialize_exception(e)
                error = {
                    'code': 400,
                    'message': 'Error',
                    'error': se
                }
                Response.status = "400 Bad Request"  
                return error
        else:
            Response.status = "401 unauthorized"
            return {'code': 401, 'error': 'Usuario no registrado o no tiene accesso a este servicio', 'message': 'error'}
    
    @http.route('/api/web/get_users/<int:user_id>', type='json', auth='user', methods=['GET'], website=False, customresp='apiresponse')
    def get_user(self, user_id):
        uid = request.session.uid

        if uid:
            if int(user_id):
                user = False
                try:
                    #get users with params
                    data = request.env['res.partner'].sudo().search([('id', '=', user_id)],limit = 1) 

                    if data and data is not False:
                        user = {
                            'id': data.id,
                            'name': data.name,
                            'ref': data.ref,
                            'email': data.email,
                            'phone': data.phone,
                            'mobile': data.mobile,
                            'vat': data.vat
                        }

                        headers = {'Content-type': 'application/json'}
                        Response.status = "200"
                        data = {'code': 200, 'user': user, 'message': 'success'}   
                        return data
                    else:
                        Response.status = "204"
                        data = {'code': 204, 'user': False, 'message': 'El usuario no existe'}   
                        return data 
                except Exception as e:
                    se = _serialize_exception(e)
                    error = {
                        'code': 400,
                        'message': 'Ocurrio un error al realizar una consulta',
                        'error': se
                    }
                    Response.status = "400 Bad Request"
                    return error            
            else:
                Response.status = "400 Bad Request"
                return {'code': 400, 'error': 'Identificador de usuario no valido', 'message': 'error'}
        else:
            Response.status = "401 unauthorized"
            return {'code': 401, 'error': 'Usuario no registrado o no tiene accesso a este servicio', 'message': 'error'}
    
    @http.route('/api/web/order', type='json', auth='user', methods=['POST'], website=False, customresp='apiresponse')
    def create_order(self, **kw):
        uid = request.session.uid

        if uid:
            try:
                partner_id = kw.get('partner_id', 0)
                partner = request.env['res.partner'].sudo().search([('id', '=', int(partner_id)),('active', '=', 'true')]) 
                
                if partner.id is not False:
                    if 'date_order' in kw:
                        date = kw.get('date_order')
                        try:
                            do = datetime.strptime(date, "%d/%m/%Y").date()
                            date_order = do.strftime('%Y-%m-%d %H:%M:%S')
                        except Exception as e:
                            se = _serialize_exception(e)
                            error = {
                                'code': 400,
                                'message': 'Error',
                                'error': e
                            }
                            Response.status = "400 Bad Request"
                            return error 
                    else:
                        error = {
                                'code': 400,
                                'message': 'Error',
                                'error': 'La peticion es incorrecta, el parametro date_order no es correcto (d/m/Y) o no existe'
                            }
                        Response.status = "400 Bad Request"
                        return error
                    
                    order_lines = kw.get('order_line', [])
                    order_line = []

                    for product in order_lines:
                        product_id = request.env['product.product'].sudo().search([('product_tmpl_id','=',product['product_id'])])
                        if product_id.id is not False:
                            order_line.append(
                                (0, 0, {
                                    'product_id': product_id.id,
                                    'product_uom_qty': product['product_uom_qty'],
                                    'price_unit': product['price_unit'],
                                    'discount': product['discount'],
                                }))
                        else:
                            error = {
                                'code': 400,
                                'message': 'Error',
                                'error': 'La peticion es incorrecta, el parametro product_id no se encuentra o no existe'
                            }
                            Response.status = "400 Bad Request"
                            return error
                    order = {
                        'partner_id': partner_id,
                        'date_order': date_order,
                        'order_line': order_line,
                    }

                    insert_order = request.env['sale.order'].sudo().create(order)
                    if insert_order.id is not False:
                        Response.status = "201 Created"
                        return {'code':201, 'order_id': insert_order.id, 'message': 'success'}
                    else:
                        error = {
                                'code': 500,
                                'message': 'Error',
                                'error': 'No se pudo registrar el pedido'
                            }
                        Response.status = "500 Server Error"
                        return error
                else:
                    error = {
                                'code': 400,
                                'message': 'Error',
                                'error': 'La peticion es incorrecta, el parametro partner_id no se encuentra o no existe'
                            }
                    Response.status = "400 Bad Request"
                    return error
            except Exception as e:
                se = _serialize_exception(e)
                error = {
                    'code': 400,
                    'message': 'Error',
                    'error': e
                }
                Response.status = "400 Bad Request"
                return error
        else:    
            Response.status = "401 unauthorized"
            return {'code': 401, 'error': 'Usuario no registrado o no tiene accesso a este servicio', 'message': 'error'}
    
    #aux - get params
    def get_params(self):
        try:
            params = request.jsonrequest['params']
            return params
        except:
            error = 'Bad Request - Los parametros son incorrectos.'
            return {'code': 400, 'error': error, 'message': 'error'}

    #this method override the default response 
    def _json_response(self, result=None, error=None):
        creponse = self.endpoint.routing.get('customresp')
        if creponse == 'apiresponse':
            response = {}
            if error is not None:
                response['error'] = error
            if result is not None:
                response = result
        else:
            response = {
                'jsonrpc': '2.0',
                'id': self.jsonrequest.get('id')
            }
            if error is not None:
                response['error'] = error
            if result is not None:
                response['result'] = result

        mime = 'application/json'
        body = json.dumps(response, default=date_utils.json_default)

        return Response(
            body, status=error and error.pop('http_status', 200) or 200,
            headers=[('Content-Type', mime), ('Content-Length', len(body))]
        )
    #overwrite the response method
    setattr(JsonRequest, '_json_response', _json_response)   
        