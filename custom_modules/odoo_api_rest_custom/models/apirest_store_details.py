import base64
import logging
from odoo import models, fields, api, _
from requests import request
import json


_logger = logging.getLogger(__name__)

class ApiRestStoreDetails(models.Model):

    _name = "apirest.store.details"

    x_api_url = fields.Char("URL", required=True, help="prestashop Store Configuration")
    x_api_db = fields.Char("Base de Datos", required=True, help="Nombre de la Base de datos.")
    x_api_username = fields.Char("Usuario", required=True, help="Nombre del usuario.")
    x_api_password = fields.Char("Password", required=True, help="Password del usuario.")