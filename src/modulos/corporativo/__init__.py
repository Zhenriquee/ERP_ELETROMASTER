from flask import Blueprint

bp_corporativo = Blueprint('corporativo', __name__, url_prefix='/corporativo')

from . import rotas