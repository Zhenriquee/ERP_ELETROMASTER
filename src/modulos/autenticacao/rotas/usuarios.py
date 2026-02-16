from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from src.extensoes import banco_de_dados as db
from src.modulos.autenticacao import bp_autenticacao
from src.modulos.autenticacao.modelos import Usuario
from src.modulos.rh.modelos import Colaborador
from src.modulos.autenticacao.formularios import FormularioUsuario, FormularioCriarAcesso
from src.modulos.autenticacao.permissoes import cargo_exigido

@bp_autenticacao.route('/usuarios', methods=['GET'])
@login_required
@cargo_exigido('rh_equipe')
def listar_usuarios():
    # Lista apenas quem TEM usuário criado
    usuarios = Usuario.query.join(Colaborador).order_by(Colaborador.nome_completo).all()
    return render_template('autenticacao/lista_usuarios.html', usuarios=usuarios)

@bp_autenticacao.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
@cargo_exigido('rh_equipe')
def novo_usuario():
    form = FormularioCriarAcesso()
    
    # Busca colaboradores que AINDA NÃO têm usuário
    colabs_sem_user = Colaborador.query.outerjoin(Usuario).filter(Usuario.id == None, Colaborador.ativo == True).all()
    form.colaborador_id.choices = [(c.id, f"{c.nome_completo} ({c.cargo_ref.nome})") for c in colabs_sem_user]
    
    if not colabs_sem_user:
        flash('Todos os colaboradores ativos já possuem acesso.', 'info')
        return redirect(url_for('autenticacao.listar_usuarios'))

    if form.validate_on_submit():
        if Usuario.query.filter_by(usuario=form.usuario.data).first():
            flash('Este login já está em uso.', 'error')
        else:
            novo = Usuario(
                colaborador_id=form.colaborador_id.data,
                usuario=form.usuario.data,
                ativo=True
            )
            novo.definir_senha(form.senha.data)
            db.session.add(novo)
            db.session.commit()
            flash('Acesso criado com sucesso!', 'success')
            return redirect(url_for('autenticacao.listar_usuarios'))
            
    return render_template('autenticacao/cadastro_usuario.html', form=form, titulo="Novo Acesso de Sistema")

@bp_autenticacao.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    
    # Regra: Admin edita todos. Usuário edita a si mesmo.
    if current_user.cargo.lower() != 'dono' and current_user.id != usuario.id:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard.painel'))

    form = FormularioUsuario(obj=usuario)
    
    if form.validate_on_submit():
        usuario.usuario = form.usuario.data
        usuario.email = form.email.data
        
        # Só altera senha se preenchida
        if form.senha.data:
            usuario.definir_senha(form.senha.data)
            
        # Apenas admin/RH pode inativar
        if current_user.tem_permissao('rh_equipe'):
            usuario.ativo = form.ativo.data
            
        db.session.commit()
        flash('Dados de acesso atualizados.', 'success')
        return redirect(url_for('autenticacao.listar_usuarios'))

    return render_template('autenticacao/cadastro_usuario.html', form=form, titulo="Editar Acesso", usuario_alvo=usuario)