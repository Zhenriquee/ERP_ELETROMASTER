from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from src.modulos.autenticacao.modelos import Usuario
from src.modulos.autenticacao.formularios import FormularioLogin, FormularioCadastroUsuario
from src.extensoes import banco_de_dados as db
from src.modulos.autenticacao.permissoes import cargo_exigido

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

@bp_autenticacao.route('/usuarios', methods=['GET'])
@login_required
@cargo_exigido('gerente') # Só gerente pra cima vê a lista
def listar_usuarios():
    usuarios = Usuario.query.all()
    return render_template('autenticacao/lista_usuarios.html', usuarios=usuarios)

@bp_autenticacao.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
@cargo_exigido('gerente') # Só gerente pra cima cadastra
def novo_usuario():
    form = FormularioCadastroUsuario()
    
    # Se o usuário não for DONO, remove o campo salário do formulário visualmente
    # e impede que ele envie dados nesse campo
    if not current_user.tem_permissao('dono'):
        del form.salario

    if form.validate_on_submit():
        # Verifica duplicidade
        if Usuario.query.filter_by(usuario=form.usuario.data).first():
            flash('Este usuário já existe.', 'error')
        elif Usuario.query.filter_by(cpf=form.cpf.data).first():
            flash('CPF já cadastrado.', 'error')
        else:
            novo_func = Usuario()
            novo_func.nome = form.nome.data
            novo_func.usuario = form.usuario.data
            novo_func.cpf = form.cpf.data
            novo_func.telefone = form.telefone.data
            novo_func.email = form.email.data
            novo_func.cargo = form.cargo.data
            novo_func.definir_senha(form.senha.data)
            
            # Lógica de Segurança do Salário
            if current_user.tem_permissao('dono'):
                novo_func.salario = form.salario.data
            else:
                novo_func.salario = 0.0 # Gerente cadastra mas não define salário

            db.session.add(novo_func)
            db.session.commit()
            flash('Funcionário cadastrado com sucesso!', 'success')
            return redirect(url_for('autenticacao.listar_usuarios'))

    return render_template('autenticacao/cadastro_usuario.html', form=form)