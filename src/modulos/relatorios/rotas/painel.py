from flask import render_template
from flask_login import login_required
from src.modulos.autenticacao.permissoes import cargo_exigido
from src.modulos.relatorios import bp_relatorios

@bp_relatorios.route('/')
@login_required
@cargo_exigido('relatorios_acesso')
def painel():
    return render_template('relatorios/painel.html')