import json
from os import access
import werkzeug
import functools

from odoo import http, api
from datetime import datetime
from odoo.http import content_disposition, request, Response, Controller , route, JsonRequest
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import date_utils
from functools import wraps

def validate_token(f):
    """."""
    @functools.wraps(f)
    def wrap(*args, **kwargs):
        try:
            authorize_token = request.httprequest.headers['Authorization']
            token =  authorize_token.split(' ')
            access_token = token[1]
            if not access_token:
                Response.status = "401 unauthorized"            
                return {'code': 401, 'error': 'no se encuentra el token de autorización', 'message': 'error'}
        
            access_token_data = (
                request.env["apirest.store.details"].sudo().search([("x_api_token", "=", access_token)], order="id DESC", limit=1)
            )

            if access_token_data.find_one_or_create_token(username = access_token_data.x_api_username, password = access_token_data.x_api_password) != access_token:
                Response.status = "401 unauthorized"
                return {'code': 401, 'error': 'El token no es valido o ya expiro', 'message': 'error'}

            user_token = access_token_data.find_user(username = access_token_data.x_api_username, password = access_token_data.x_api_password)
            if not user_token:
                Response.status = "401 unauthorized"
                return {'code': 401, 'error': 'El usuario no esta registrado o no existe, verifique los datos.', 'message': 'error'}

            request.session.uid = user_token.id
            request.uid = user_token.id
            return f(*args, **kwargs)
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 400,
                'message': 'Error',
                'error': se
            }
            Response.status = "400 Bad Request"
            return error
    return wrap

class ApiAccess(http.Controller):

    def __init__(self):
        self._model = "ir.model"

    @http.route('/api/web/authenticate', type='json', auth='none', methods=['GET'], website=False, csrf=False, customresp='apiresponse')
    def authenticate(self, login, password):
            Response.status = "200"
            return {'code': 200, 'error': 'Metodo ya no utilizado, dirijase al backoffice de Oddo para obtener el token.', 'message': 'info'}

    @validate_token
    @http.route('/api/web/get_products/<int:user_id>', type='json', auth='none', methods=['GET'], website=False, csrf=False, customresp='apiresponse')
    def get_products(self, **kw):       
        try:
            user_id = kw.get('user_id', 0)
            if int(user_id) > 0:
                products = []
                params = self.get_api_params()

                if params.get('error') is not None:
                    error = {
                        'code': 400,
                        'message': 'Error',
                        'error': params.get('error')
                    }
                    Response.status = "400 Bad Request"
                    return error
                else:
                    page = params.get('page')
                    step = params.get('step')
                    limit= params.get('limit')
                
                user = request.env['res.partner'].sudo().search([('id', '=', int(user_id))], order ='id asc', limit = 1)
                all_products = user.property_product_pricelist if len(user) > 0 else [] #user.property_product_pricelist.item_ids 
                products_by_user = all_products.item_ids if len(all_products) > 0 else []
    
                for prods in products_by_user:
                    for p in prods.product_tmpl_id:
                        sellers = []
                        price = 0.0

                        if prods.fixed_price:
                            price = prods.fixed_price

                        for s in p.seller_ids:
                            sellers.append(s.name.name)
        
                        item = {
                            'id': p.id,
                            'default_code': p.default_code,
                            'description_sale': p.description_sale,
                            'price': price,
                            'weight': p.weight,
                            'categ_id': p.categ_id.id,
                            'x_manufacturer_code': p.x_manufacturer_code if hasattr(p,'x_manufacturer_code') else '',
                            'seller_ids': ", ".join(sellers)
                        }
                        products.append(item)
                Response.status = "200"  
                return {'code': 200, 'products': products, 'message': 'success'}
            else:
                Response.status = "400 Bad Request"
                return {'code': 400, 'error': 'Identificador de usuario no valido', 'message': 'error'}
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 400,
                'message': 'Error',
                'error': se
            }
            Response.status = "400 Bad Request"
            return error

    @validate_token
    @http.route('/api/web/get_categories', type='json', auth='none', methods=['GET'], website=False, csrf=False, customresp='apiresponse')
    def get_categories(self):
        try:
            categories = []
            params = self.get_api_params()

            if params.get('error') is not None:
                error = {
                    'code': 400,
                    'message': 'Error',
                    'error': params.get('error')
                }
                Response.status = "400 Bad Request"
                return error
            else:
                page = params.get('page')
                step = params.get('step')
                limit= params.get('limit')
            
            all_category = request.env['product.category'].sudo().search([], order = 'id asc', offset = (page - 1) * step, limit = limit) 

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
    
    @validate_token
    @http.route('/api/web/get_users', type='json', auth='none', methods=['GET'], website=False, csrf=False, customresp='apiresponse')
    def get_users(self):
        try:
            users = []
            params = self.get_api_params()

            if params.get('error') is not None:
                error = {
                    'code': 400,
                    'message': 'Error',
                    'error': params.get('error')
                }
                Response.status = "400 Bad Request"
                return error
            else:
                page = params.get('page')
                step = params.get('step')
                limit= params.get('limit')
        
            #get users with params
            all_users = request.env['res.partner'].sudo().search([('active', '=', 'true')], order = 'id asc', offset = (page - 1) * step, limit = limit) 

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

    @validate_token
    @http.route('/api/web/get_product_image', type='json', auth='none', methods=['GET'], csrf=False, website=False, customresp='apiresponse')
    def get_product_image(self, product_id):
            try:
                if int(product_id):
                    #get users with params
                    product = request.env['product.template'].sudo().search([('id', '=', int(product_id)),('image_1920', '!=', False)], limit = 1)
                    if product:
                        image = product.image_1920
                        Response.status = "200"
                        return {'code':200, 'image': image, 'message':'success'}
                    else: 
                        Response.status = "200"
                        return {'code':200, 'image': False, 'message':'success'}
                else:
                    error = {
                        'code': 400,
                        'message': 'Ocurrio un error al realizar una consulta, verifique el valor del product_id, debe ser un numero.',
                        'error': 'La peticion es incorrecta, el id del producto no se encuentra o no existe.'
                    }
                    Response.status = "400 Bad Request"
                    return error  
            except Exception as e:
                se = _serialize_exception(e)
                error = {
                    'code': 400,
                    'message': 'Ocurrio un error al realizar una consulta, verifique el valor del product_id, debe ser un numero',
                    'error': se
                }
                Response.status = "400 Bad Request"
                return error        
    
    @validate_token
    @http.route('/api/web/get_users/<int:user_id>', type='json', auth='none', methods=['GET'], csrf=False, website=False, customresp='apiresponse')
    def get_user(self, **kw):
        try:
            user_id = kw.get('user_id', 0)
            if int(user_id) > 0:
                user = False
                #get users with params
                data = request.env['res.partner'].sudo().search([('id', '=', int(user_id))],limit = 1) 

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
            else:
                Response.status = "400 Bad Request"
                return {'code': 400, 'error': 'Identificador de usuario no valido', 'message': 'error'}
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 400,
                'message': 'Ocurrio un error al realizar una consulta, verifique el identificador de usuario.',
                'error': se
            }
            Response.status = "400 Bad Request"
            return error            
        

    
    @validate_token
    @http.route('/api/web/order', type='json', auth='none', methods=['POST'], website=False, csrf=False, customresp='apiresponse')
    def create_order(self, **kw):
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
    
    #aux - get params
    def get_api_params(self):
        try:
            params = request.jsonrequest.get('params',{})
            result = {}
            # valores de busqueda por defecto    
            page = 1
            step = 1000 
            limit= 1000
            
            if 'page' in params:
                page = int(request.params['page']) if int(request.params['page']) > 0 else False

            if 'limit' in params:
                limit = int(request.params['limit']) if int(request.params['limit']) > 0 else False
                step = limit

            if limit is False or page is False:
                error = 'Parametros incorrectos, page y limit deben ser numeros mayores a 0.'            
                result = {'error': error, 'status': False}
            else:
                result = {'page': page, 'limit': limit, 'step': step}
            return result

        except Exception as e:
            error = 'Parametros incorrectos, page y limit deben ser numeros mayores a 0.'            
            result = {'error': error, 'status': False}
            return result 

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
        