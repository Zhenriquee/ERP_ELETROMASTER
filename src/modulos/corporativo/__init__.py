from flask import Blueprint, redirect, url_for, flash
from flask_login import current_user

bp_corporativo = Blueprint('corporativo', __name__, url_prefix='/corporativo')

# --- TRAVA DE SEGURANÇA GLOBAL DO MÓDULO ---
@bp_corporativo.before_request
def restringir_acesso_dono():
    # 1. Se o usuário não estiver logado, manda pro login
    if not current_user.is_authenticated:
        return redirect(url_for('autenticacao.login'))
        
    # 2. Pega o nome do cargo do usuário logado (tudo em minúsculo para evitar erro de digitação)
    cargo_atual = current_user.cargo.lower() if current_user.cargo else ''
    
    # 3. Se não for o dono, bloqueia o acesso e devolve pro Dashboard
    if cargo_atual != 'dono':
        flash('Acesso Restrito: Apenas contas com cargo de "Dono" podem acessar Cargos e Setores.', 'error')
        return redirect(url_for('dashboard.painel'))

# A importação das rotas precisa ficar aqui no final para evitar erro de referência cruzada
from . import rotas