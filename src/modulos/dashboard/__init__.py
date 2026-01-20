from flask import Blueprint

bp_dashboard = Blueprint('dashboard', __name__, url_prefix='/dashboard')

from . import rotas