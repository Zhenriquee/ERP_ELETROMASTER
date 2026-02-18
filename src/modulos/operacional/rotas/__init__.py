from flask import Blueprint

bp_operacional = Blueprint('operacional', __name__, url_prefix='/operacional')

from . import painel, acoes