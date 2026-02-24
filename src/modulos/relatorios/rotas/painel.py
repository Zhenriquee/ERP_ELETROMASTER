from flask import render_template, flash, redirect, url_for
from flask_login import login_required, current_user
from src.modulos.relatorios import bp_relatorios

@bp_relatorios.route('/')
@login_required
def painel():
    # Verifica se é dono ou se tem pelo menos uma permissão de relatório
    eh_dono = current_user.cargo and current_user.cargo.lower() == 'dono'
    tem_alguma = (
        current_user.tem_permissao('relatorios_servicos') or 
        current_user.tem_permissao('relatorios_consumo') or 
        current_user.tem_permissao('relatorios_financeiro')
    )
    
    if not (tem_alguma or eh_dono):
        flash('Você não possui permissão para acessar os relatórios.', 'error')
        return redirect(url_for('dashboard.painel'))
        
    return render_template('relatorios/painel.html')