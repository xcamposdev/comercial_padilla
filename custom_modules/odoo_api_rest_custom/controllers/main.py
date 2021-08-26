import json
import functools
from datetime import datetime
from odoo.http import request, Response, Controller, route, JsonRequest
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import date_utils


def validate_token(f):
    """."""

    @functools.wraps(f)
    def wrap(*args, **kwargs):
        try:
            authorize_token = request.httprequest.headers['Authorization']
            token = authorize_token.split(' ')
            access_token = token[1]
            if not access_token:
                return {
                    'code': 401,
                    'message': '401 unauthorized',
                    'error': 'no se encuentra el token de autorización'
                }

            access_token_data = request.env["apirest.store.details"].sudo().search([("x_api_token", "=", access_token)],
                                                                   order="id DESC", limit=1)

            if access_token_data.find_one_or_create_token(username=access_token_data.x_api_username,
                                                          password=access_token_data.x_api_password) != access_token:
                return {
                    'code': 401,
                    'message': '401 unauthorized',
                    'error': 'El token no es valido o ya expiro'
                }
            return f(*args, **kwargs)
        except Exception as e:
            se = _serialize_exception(e)
            return {
                'code': 401,
                'message': '401 unauthorized',
                'error': 'El token no es valido o ya expiro'
            }

    return wrap


class ApiAccess(Controller):

    @route('/api/web/authenticate', type='json', auth='none', methods=['GET'], website=False, csrf=False,
           customresp='apiresponse')
    def authenticate(self, login, password):
        return {'code': 200, 'error': 'Metodo ya no utilizado, dirijase al backoffice de Oddo para obtener el token.',
                'message': 'info'}

    @validate_token
    @route('/api/web/get_products/<int:user_id>', type='json', auth='none', methods=['GET'], website=False, csrf=False, customresp='apiresponse')
    def get_products(self, user_id=None):
        try:
            if user_id:
                products = []
                params = self.get_api_params()

                if params.get('error') is not None:
                    return {
                        'code': 400,
                        'message': '400: Bad Request',
                        'error': params.get('error')
                    }
                else:
                    # TODO: the pagination is not enabled
                    page = params.get('page')
                    step = params.get('step')
                    limit = params.get('limit')

                product_pl_items = request.env['product.pricelist.item']
                product_pl_items = product_pl_items.sudo().search([('x_studio_presupuestar_a.id', '=', int(user_id))])
                location_code = request.env['ir.config_parameter'].sudo().get_param('odoo_api_rest_custom'
                                                                                 '.x_location_code') or False
                if not location_code:
                    location_code = 'CIN'

                for prods in product_pl_items:
                    sellers = {}
                    price = 0.0

                    if prods.fixed_price:
                        price = prods.fixed_price

                    for s in prods.product_tmpl_id.seller_ids:
                        sellers.append(s.name.name)

                    for p in prods.product_tmpl_id.product_variant_ids:
                        stock_qty = request.env['stock.quant'].sudo().search([
                            ('product_id', '=', p.id),
                            ('location_id.complete_name', 'ilike', location_code), ('quantity', '>', 0)])

                        on_hand = 0

                        for sq in stock_qty:
                            on_hand += sq.quantity

                        item = {
                            'id': p.id,
                            'default_code': p.default_code,
                            'description_sale': p.description_sale,
                            'price': price,
                            'weight': p.weight,
                            'categ_id': p.categ_id.id,
                            'x_manufacturer_code': p.x_manufacturer_code if hasattr(p, 'x_manufacturer_code') else '',
                            'seller_ids': ", ".join(list(sellers)),
                            'quantity': on_hand,
                        }
                        products.append(item)
                return {'code': 200, 'products': products, 'message': 'success'}
            else:
                return {
                    'code': 400,
                    'error': 'Identificador de usuario no valido',
                    'message': '400 Bad Request'}
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 400,
                'message': '400 Bad Request',
                'error': se
            }
            return error

    @validate_token
    @route('/api/web/get_categories', type='json', auth='none', methods=['GET'], website=False, csrf=False,
           customresp='apiresponse')
    def get_categories(self):
        try:
            categories = []
            params = self.get_api_params()

            if params.get('error') is not None:
                error = {
                    'code': 400,
                    'message': '400 Bad Request',
                    'error': params.get('error')
                }
                return error
            else:
                page = params.get('page')
                step = params.get('step')
                limit = params.get('limit')

            all_category = request.env['product.category'].sudo().search([], order='id asc', offset=(page - 1) * step,
                                                                         limit=limit)

            for c in all_category:
                item = {
                    'id': c.id,
                    'name': c.name,
                    'parent_id': c.parent_id.id
                }
                categories.append(item)
            return {'code': 200, 'categories': categories, 'message': 'success'}
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 400,
                'message': '400 Bad Request',
                'error': se
            }
            return error

    @validate_token
    @route('/api/web/get_users', type='json', auth='none', methods=['GET'], website=False, csrf=False,
           customresp='apiresponse')
    def get_users(self):
        try:
            users = []
            params = self.get_api_params()

            if params.get('error') is not None:
                error = {
                    'code': 400,
                    'message': '400 Bad Request',
                    'error': params.get('error')
                }
                return error
            else:
                page = params.get('page')
                step = params.get('step')
                limit = params.get('limit')

            # get users with params
            all_users = request.env['res.partner'].sudo().search([('active', '=', 'true')], order='id asc',
                                                                 offset=(page - 1) * step, limit=limit)

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

            data = {'code': 200, 'users': users, 'message': 'success'}
            return data

        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 500,
                'message': '500 Internal server error',
                'error': se
            }
            return error

    @validate_token
    @route('/api/web/get_product_image', type='json', auth='none', methods=['GET'], csrf=False, website=False,
           customresp='apiresponse')
    def get_product_image(self, product_id):
        try:
            if int(product_id):
                # get users with params
                product = request.env['product.template'].sudo().search(
                    [('id', '=', int(product_id)), ('image_1920', '!=', False)], limit=1)
                if product:
                    image = product.image_1920
                    return {'code': 200, 'image': image, 'message': 'success'}
                else:
                    return {'code': 200, 'image': False, 'message': 'success'}
            else:
                error = {
                    'code': 400,
                    'message': '400 Bad Request',
                    'error': 'La peticion es incorrecta, el id del producto no se encuentra o no existe.'
                }
                return error
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 500,
                'message': '500 Internal server error',
                'error': se
            }
            return error

    @validate_token
    @route('/api/web/get_users/<int:user_id>', type='json', auth='none', methods=['GET'], csrf=False, website=False,
           customresp='apiresponse')
    def get_user(self, user_id=None):
        try:
            if user_id:
                user = False
                # get users with params
                data = request.env['res.partner'].sudo().search([('id', '=', int(user_id))], limit=1)

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

                    data = {'code': 200, 'user': user, 'message': 'success'}
                    return data
                else:
                    data = {'code': 204, 'user': False, 'message': 'El usuario no existe'}
                    return data
            else:
                return {'code': 400, 'error': 'Identificador de usuario no valido', 'message': '400 Bad Request'}
        except Exception as e:
            se = _serialize_exception(e)
            return {
                'code': 500,
                'message': '500 Internal server error',
                'error': 'Ocurrio un error al realizar una consulta, verifique el identificador de usuario: {}'.format(se)
            }

    @validate_token
    @route('/api/web/order', type='json', auth='none', methods=['POST'], website=False, csrf=False,
           customresp='apiresponse')
    def create_order(self, **kw):
        try:
            partner_id = kw.get('partner_id', 0)
            partner = request.env['res.partner'].sudo().search([('id', '=', int(partner_id)), ('active', '=', 'true')])

            if partner.id is not False:
                if 'date_order' in kw:
                    date = kw.get('date_order')
                    try:
                        do = datetime.strptime(date, "%d/%m/%Y").date()
                        date_order = do.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception as e:
                        se = _serialize_exception(e)
                        error = {
                            'code': 500,
                            'message': '500 Internal server error',
                            'error': e
                        }
                        return error
                else:
                    error = {
                        'code': 400,
                        'message': '400 Bad Request',
                        'error': 'La peticion es incorrecta, el parametro date_order no es correcto (d/m/Y) o no existe'
                    }
                    return error

                order_lines = kw.get('order_line', [])
                order_line = []

                for product in order_lines:
                    product_id = request.env['product.product'].sudo().search(
                        [('product_tmpl_id', '=', product['product_id'])])
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
                            'message': '400 Bad Request',
                            'error': 'La peticion es incorrecta, el parametro product_id no se encuentra o no existe'
                        }
                        return error
                order = {
                    'partner_id': partner_id,
                    'date_order': date_order,
                    'order_line': order_line,
                }

                insert_order = request.env['sale.order'].sudo().create(order)
                if insert_order.id is not False:
                    return {'code': 201, 'order_id': insert_order.id, 'message': 'success'}
                else:
                    error = {
                        'code': 500,
                        'message': '500 Internal server error',
                        'error': 'No se pudo registrar el pedido'
                    }
                    return error
            else:
                error = {
                    'code': 400,
                    'message': '400 Bad Request',
                    'error': 'La peticion es incorrecta, el parametro partner_id no se encuentra o no existe'
                }
                return error
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 500,
                'message': '500 Internal server error',
                'error': e
            }
            return error

    # aux - get params
    def get_api_params(self):
        try:
            params = request.jsonrequest.get('params', {})
            result = {}
            # valores de busqueda por defecto    
            page = 1
            step = 1000
            limit = 1000

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

    # # this method override the default response
    def _json_response(self, result=None, error=None):
        creponse = self.endpoint.routing.get('customresp')
        if creponse == 'apiresponse':
            response = {}
            if error is not None:
                response['error'] = error
            if result is not None:
                response = result
                if 'error' in result:
                    error = {
                        'http_status': result['code'],
                        'code': result['code'],
                        'message': result['message']
                    }
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

    # overwrite the response method
    setattr(JsonRequest, '_json_response', _json_response)
