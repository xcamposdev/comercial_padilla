import base64
import logging
import json
import hashlib
import os
import uuid

from datetime import datetime, timedelta
from odoo import models, fields, api, _
from requests import request
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

class ApiRestStoreDetails(models.Model):

    _name = "apirest.store.details"

    x_api_db = fields.Char("Base de Datos", required=True, help="Nombre de la Base de datos.")
    x_api_username = fields.Char("Usuario", required=True, help="Nombre del usuario.")
    x_api_password = fields.Char("Password", required=True, help="Password del usuario.")
    x_api_token_expire_days = fields.Char("Validez Token(Nº de dias)", required=True, default="5", help="tiempo en dias de la validez del tokena partir de hoy, por defecto 5 dias.")
    x_api_token = fields.Char("Token", readonly=True, help="Token que permite consultar el API.")
    x_api_token_expire = fields.Char("Validez del Token", readonly=True, help="Fecha de caducidad del Token.")

    def find_one_or_create_token(self, username=None, password=None, create=False):
        if not username:
            user_id = self.env.user.id
        
        access_token = self.env["apirest.store.details"].sudo().search([("x_api_username", "=", username), ("x_api_password", "=", password)], order="id DESC", limit=1)
        
        if access_token:
            access_token = access_token[0]
            if access_token.has_expired():
                access_token = None
        if not access_token and create:
            expires = datetime.now() + timedelta(seconds=int(432000))
            self.generate_new_token()
            vals = {
                'x_api_db': self.x_api_db,
                'x_api_username': self.x_api_username,
                'x_api_password': self.x_api_password,
                "x_api_token_expire_days": 5,
                "x_api_token_expire": expires.strftime(DEFAULT_SERVER_DATE_FORMAT),
                "x_api_token": self.x_api_token
            }
            access_token = self.env["apirest.store.details"].sudo().create(vals)
            return access_token
        if not access_token:
            return None
        return access_token.x_api_token
    
    def find_user(self, username=None, password=None):
        id_user = self.env["res.users"].sudo().search([('login', '=', username), ('password', '=', password)], order="id DESC", limit=1)
        if id_user.id:
            return id_user
        return None 
    
    def has_expired(self):
        self.ensure_one()
        now = datetime.now()
        expire = fields.Datetime.from_string(self.x_api_token_expire)
        return now > expire
    
    def generate_new_token(self, context=None):
        self.ensure_one()
        _logger.info('Se esta generando el token')
        # rbytes = os.urandom(40)
        # total = str(hashlib.sha256(rbytes).hexdigest())
        # Convert a UUID to a 32-character hexadecimal string
        token = uuid.uuid4().hex
        days = int(self.x_api_token_expire_days) if int(self.x_api_token_expire_days) > 0 else 5
        expires = datetime.now() + timedelta(seconds=int(86400 * (days)))
        # Fecha de expiracion en formato Y-m-d
        date_format = expires.strftime(DEFAULT_SERVER_DATE_FORMAT)
        _logger.info(token)
        _logger.info(date_format)
        if token:
            self.x_api_token = token
            self.x_api_token_expire = date_format
