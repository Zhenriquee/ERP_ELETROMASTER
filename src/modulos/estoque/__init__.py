from flask import Blueprint

bp_estoque = Blueprint('estoque', __name__, url_prefix='/estoque')

from . import rotas