from .rotas import bp_autenticacao
from .modelos import Usuario
from src.extensoes import login_manager

@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))