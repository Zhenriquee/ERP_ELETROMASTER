from flask import redirect,flash,render_template, url_for
from flask_login import login_required, current_user
from src.modulos.autenticacao.permissoes import cargo_exigido
from src.modulos.relatorios import bp_relatorios

@bp_relatorios.route('/')
@login_required
@cargo_exigido('relatorios_acesso')
def painel():
    # Se não tiver acesso a NENHUM relatório, chuta de volta pro dashboard inicial
    if not (current_user.tem_permissao('relatorios_servicos') or current_user.tem_permissao('relatorios_financeiro')):
        flash('Você não possui permissões para visualizar relatórios.', 'error')
        return redirect(url_for('dashboard.painel'))
        
    return render_template('relatorios/painel.html')