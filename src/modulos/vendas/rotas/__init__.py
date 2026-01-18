from flask import Blueprint

# 1. Cria o Blueprint (igual fazia antes)
bp_vendas = Blueprint('vendas', __name__, url_prefix='/vendas')

# 2. Importa as rotas divididas
# O ponto (.) significa "desta pasta atual"
from . import gestao, criacao, acoes, financeiro, api