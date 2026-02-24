from flask import Blueprint

bp_relatorios = Blueprint('relatorios', __name__, url_prefix='/relatorios')

# Importa as rotas da nova subpasta
from .rotas import painel, servicos, consumo