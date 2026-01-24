from flask import Blueprint
from src.extensoes import login_manager
from src.modulos.autenticacao.modelos import Usuario

# Cria o Blueprint
bp_autenticacao = Blueprint('autenticacao', __name__, url_prefix='/auth')

# --- CORREÇÃO DO ERRO ---
# Função obrigatória do Flask-Login para carregar o usuário da sessão
@login_manager.user_loader
def load_user(user_id):
    # Retorna o usuário do banco ou None se não existir
    return Usuario.query.get(int(user_id))

# Importa as rotas para registrar no Blueprint
# (Importante: deve ficar NO FINAL para evitar importação circular)
from . import rotas