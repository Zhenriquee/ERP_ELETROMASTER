from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from src.modulos.autenticacao.modelos import Usuario
from src.modulos.autenticacao.formularios import FormularioLogin

bp_autenticacao = Blueprint('autenticacao', __name__, url_prefix='/auth')

@bp_autenticacao.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('verificacao_saude'))

    form = FormularioLogin()

    if form.validate_on_submit():
        # BUSCA PELO USUARIO (LOGIN)
        user_banco = Usuario.query.filter_by(usuario=form.usuario.data).first()

        if user_banco and user_banco.verificar_senha(form.senha.data):
            login_user(user_banco, remember=form.lembrar_de_mim.data)
            flash(f'Bem-vindo, {user_banco.nome}!', 'success')
            
            proxima_pagina = request.args.get('next')
            return redirect(proxima_pagina or url_for('verificacao_saude'))
        else:
            flash('Usuário ou senha incorretos.', 'error')

    return render_template('autenticacao/login.html', form=form)

@bp_autenticacao.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('autenticacao.login'))