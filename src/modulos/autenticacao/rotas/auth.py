from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from src.modulos.autenticacao import bp_autenticacao
from src.modulos.autenticacao.modelos import Usuario
from src.modulos.autenticacao.formularios import FormularioLogin

@bp_autenticacao.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.painel'))
    
    form = FormularioLogin()
    if form.validate_on_submit():
        user_banco = Usuario.query.filter_by(usuario=form.usuario.data).first()
        
        if user_banco and user_banco.verificar_senha(form.senha.data):
            # --- VALIDAÇÃO DE USUÁRIO ATIVO ---
            if not user_banco.ativo:
                flash('Este usuário foi inativado. Contate o administrador.', 'error')
                return render_template('autenticacao/login.html', form=form)
            # ----------------------------------

            login_user(user_banco, remember=form.lembrar_de_mim.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.painel'))
        else:
            flash('Usuário ou senha incorretos.', 'error')
    return render_template('autenticacao/login.html', form=form)

@bp_autenticacao.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('autenticacao.login'))

# --- ADICIONE ESTA NOVA ROTA NO FINAL ---
@bp_autenticacao.route('/suspenso')
def sistema_suspenso():
    """Rota para exibir a tela de bloqueio por falta de pagamento/licença"""
    return render_template('erros/pagamento.html')