import json
import logging
import werkzeug

from odoo import http
from odoo.http import content_disposition, request, Response, Controller , route, JsonRequest
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import date_utils
from odoo.tools import html_escape
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

    @http.route('/api/web/get_products', type='json', auth='user', methods=['POST'], website=False, customresp='apiresponse')
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
                    item = {
                        'id': p.id,
                        'default_code': p.default_code,
                        'description_sale': p.description_sale,
                        'weight': p.weight,
                        'categ_id': p.categ_id.id,
                        'x_manufacturar_code': p.x_manufacturar_code if hasattr(p,'x_manufacturar_code') else '',
                        'image': p.image_1920,
                        'seller_ids':p.seller_ids.name.name
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

    @http.route('/api/web/get_categories', type='json', auth='user', methods=['POST'], website=False, customresp='apiresponse')
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
    
    @http.route('/api/web/get_users', type='json', auth='user', methods=['POST'], website=False, customresp='apiresponse')
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
    
    @http.route('/api/web/get_users/<int:user_id>', type='json', auth='user', methods=['POST'], website=False, customresp='apiresponse')
    def get_user(self, user_id):
        uid = request.session.uid

        if uid:
            if int(user_id):
                user = False
                try:
                    #get users with params
                    data = request.env['res.partner'].sudo().search([('id', '=', user_id)],limit = 1) 

                    if data:
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
    def create_order(self):
        _logger.info('entro')
        return True
    
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
        