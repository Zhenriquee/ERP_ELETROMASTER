from flask import Blueprint

bp_relatorios = Blueprint('relatorios', __name__, url_prefix='/relatorios')

from . import rotas