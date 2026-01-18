from flask import Blueprint

bp_metas = Blueprint('metas', __name__, url_prefix='/metas')

from . import definicao, monitoramento