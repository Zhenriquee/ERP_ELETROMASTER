from flask import Blueprint

bp_rh = Blueprint('rh', __name__, url_prefix='/rh')

from . import rotas