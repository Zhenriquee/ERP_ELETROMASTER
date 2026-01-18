from flask import Blueprint

# Cria o Blueprint
bp_financeiro = Blueprint('financeiro', __name__, url_prefix='/financeiro')

# Importa as rotas divididas para que o Flask as reconheça
from . import painel, lancamentos, fornecedores, acoes