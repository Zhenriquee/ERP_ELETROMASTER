import os
from flask import render_template, redirect, url_for, flash, request, send_from_directory, current_app
from flask_login import login_required, current_user
from wtforms.validators import Optional
from werkzeug.utils import secure_filename
from src.extensoes import banco_de_dados as db
from src.modulos.autenticacao import bp_autenticacao
from src.modulos.autenticacao.modelos import Usuario, Modulo, DocumentoUsuario
from src.modulos.autenticacao.formularios import FormularioCadastroUsuario, FormularioDocumento
from src.modulos.autenticacao.permissoes import cargo_exigido
from datetime import datetime

@bp_autenticacao.route('/usuarios', methods=['GET'])
@login_required
@cargo_exigido('rh_equipe') 
def listar_usuarios():
    usuarios = Usuario.query.all()
    return render_template('autenticacao/lista_usuarios.html', usuarios=usuarios)

# FUNÇÃO AUXILIAR PARA AGRUPAR MÓDULOS (ATUALIZADA)
def agrupar_modulos(todos_modulos):
    grupos = {
        'Dashboard': [],
        'Vendas': [],
        'Gestão': [],
        'Admin': []
    }
    
    for m in todos_modulos:
        if m.codigo.startswith('dash_'):
            grupos['Dashboard'].append(m)
        elif m.codigo.startswith('vendas_'):
            grupos['Vendas'].append(m)
        elif m.codigo in ['producao_operar', 'estoque_gerir', 'metas_equipe']:
            grupos['Gestão'].append(m)
        elif m.codigo in ['financeiro_acesso', 'rh_equipe', 'rh_salarios']:
            grupos['Admin'].append(m)
            
    return grupos

# --- ROTA NOVO USUÁRIO ---
@bp_autenticacao.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
@cargo_exigido('rh_equipe') 
def novo_usuario():
    form = FormularioCadastroUsuario()
    
    opcoes_cargos = [('dono', 'Dono', 1), ('gerente', 'Gerente', 2), ('coordenador', 'Coordenador', 3), ('tecnico', 'Técnico', 4)]
    form.cargo.choices = [(v, n) for v, n, l in opcoes_cargos if l >= current_user.nivel_acesso]

    todos_modulos = Modulo.query.order_by(Modulo.nome).all()
    if current_user.cargo != 'dono':
        ids_meus = [m.id for m in current_user.permissoes]
        todos_modulos = [m for m in todos_modulos if m.id in ids_meus]

    form.modulos_acesso.choices = [(m.id, m.nome) for m in todos_modulos]
    modulos_grupos = agrupar_modulos(todos_modulos)

    if current_user.cargo != 'dono' and not current_user.tem_permissao('rh_salarios'):
        del form.salario

    if form.validate_on_submit():
        if Usuario.query.filter_by(usuario=form.usuario.data).first():
            flash('Este usuário já existe.', 'error')
        else:
            novo_func = Usuario()
            novo_func.nome = form.nome.data
            novo_func.usuario = form.usuario.data
            novo_func.cpf = form.cpf.data
            novo_func.telefone = form.telefone.data
            novo_func.cargo = form.cargo.data
            novo_func.equipe = form.equipe.data
            novo_func.ativo = form.ativo.data
            novo_func.definir_senha(form.senha.data)
            
            if hasattr(form, 'salario'): novo_func.salario = form.salario.data
            ids_selecionados = form.modulos_acesso.data
            novo_func.permissoes = Modulo.query.filter(Modulo.id.in_(ids_selecionados)).all()

            db.session.add(novo_func)
            db.session.commit()
            flash('Funcionário cadastrado!', 'success')
            return redirect(url_for('autenticacao.listar_usuarios'))

    return render_template('autenticacao/cadastro_usuario.html', form=form, modulos_grupos=modulos_grupos)

# --- ROTA EDITAR USUÁRIO ---
@bp_autenticacao.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_usuario(id):
    usuario_edit = Usuario.query.get_or_404(id)
    
    if current_user.cargo != 'dono' and current_user.id != usuario_edit.id:
        flash('Você não tem permissão para editar outros usuários.', 'error')
        return redirect(url_for('autenticacao.listar_usuarios'))

    form = FormularioCadastroUsuario(obj=usuario_edit)
    form.senha.validators = [Optional()]

    opcoes_cargos = [('dono', 'Dono'), ('gerente', 'Gerente'), ('coordenador', 'Coordenador'), ('tecnico', 'Técnico')]
    
    if current_user.cargo == 'dono':
        form.cargo.choices = opcoes_cargos
    else:
        form.cargo.choices = [(usuario_edit.cargo, usuario_edit.cargo.title())]

    todos_modulos = Modulo.query.order_by(Modulo.nome).all()
    form.modulos_acesso.choices = [(m.id, m.nome) for m in todos_modulos]
    modulos_grupos = agrupar_modulos(todos_modulos)

    if current_user.cargo != 'dono' and not current_user.tem_permissao('rh_salarios'):
        del form.salario

    if request.method == 'GET':
        form.modulos_acesso.data = [m.id for m in usuario_edit.permissoes]
        form.ativo.data = usuario_edit.ativo
        form.equipe.data = usuario_edit.equipe

    if form.validate_on_submit():
        check_user = Usuario.query.filter(Usuario.usuario == form.usuario.data, Usuario.id != id).first()
        if check_user:
            flash(f'O login "{form.usuario.data}" já está em uso.', 'error')
            return render_template('autenticacao/cadastro_usuario.html', form=form, editando=True, modulos_grupos=modulos_grupos)
        
        usuario_edit.usuario = form.usuario.data
        usuario_edit.email = form.email.data
        usuario_edit.telefone = form.telefone.data
        
        if form.senha.data:
            usuario_edit.definir_senha(form.senha.data)

        if current_user.cargo == 'dono':
            usuario_edit.nome = form.nome.data
            usuario_edit.cpf = form.cpf.data
            usuario_edit.cargo = form.cargo.data
            usuario_edit.equipe = form.equipe.data
            usuario_edit.ativo = form.ativo.data
            if hasattr(form, 'salario'): usuario_edit.salario = form.salario.data
            usuario_edit.permissoes = Modulo.query.filter(Modulo.id.in_(form.modulos_acesso.data)).all()
        
        try:
            db.session.commit()
            flash('Perfil atualizado com sucesso!', 'success')
            if current_user.id == usuario_edit.id:
                 return redirect(url_for('dashboard.painel'))
            return redirect(url_for('autenticacao.listar_usuarios'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao salvar dados.', 'error')

    return render_template('autenticacao/cadastro_usuario.html', form=form, editando=True, modulos_grupos=modulos_grupos)

@bp_autenticacao.route('/usuarios/<int:id>/documentos', methods=['GET', 'POST'])
@login_required
@cargo_exigido('rh_equipe')
def gerenciar_documentos(id):
    usuario_alvo = Usuario.query.get_or_404(id)
    form = FormularioDocumento()
    
    upload_path = current_app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)

    if form.validate_on_submit():
        arquivo = form.arquivo.data
        filename_original = secure_filename(arquivo.filename)
        extensao = filename_original.rsplit('.', 1)[1].lower() if '.' in filename_original else ''
        novo_nome = f"{usuario_alvo.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{extensao}"
        caminho_completo = os.path.join(upload_path, novo_nome)
        arquivo.save(caminho_completo)
        tamanho = os.path.getsize(caminho_completo) / 1024

        doc = DocumentoUsuario(
            usuario_id=usuario_alvo.id,
            nome_arquivo=novo_nome,
            nome_original=form.descricao.data,
            tipo_arquivo=extensao,
            tamanho_kb=tamanho,
            enviado_por_id=current_user.id
        )
        db.session.add(doc)
        db.session.commit()
        flash('Documento anexado com sucesso!', 'success')
        return redirect(url_for('autenticacao.gerenciar_documentos', id=usuario_alvo.id))

    documentos = DocumentoUsuario.query.filter_by(usuario_id=usuario_alvo.id).order_by(DocumentoUsuario.criado_em.desc()).all()
    return render_template('autenticacao/documentos.html', usuario=usuario_alvo, form=form, documentos=documentos)

@bp_autenticacao.route('/documentos/baixar/<int:doc_id>')
@login_required
@cargo_exigido('rh_equipe')
def baixar_documento(doc_id):
    doc = DocumentoUsuario.query.get_or_404(doc_id)
    path = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(path, doc.nome_arquivo, as_attachment=True, download_name=f"{doc.nome_original}.{doc.tipo_arquivo}")

@bp_autenticacao.route('/documentos/visualizar/<int:doc_id>')
@login_required
@cargo_exigido('rh_equipe')
def visualizar_documento(doc_id):
    doc = DocumentoUsuario.query.get_or_404(doc_id)
    path = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(path, doc.nome_arquivo, as_attachment=False)

@bp_autenticacao.route('/documentos/deletar/<int:doc_id>')
@login_required
@cargo_exigido('rh_equipe')
def deletar_documento(doc_id):
    doc = DocumentoUsuario.query.get_or_404(doc_id)
    usuario_id = doc.usuario_id
    try:
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], doc.nome_arquivo)
        if os.path.exists(path):
            os.remove(path)
        db.session.delete(doc)
        db.session.commit()
        flash('Documento removido.', 'success')
    except Exception as e:
        flash(f'Erro ao deletar: {str(e)}', 'error')
    return redirect(url_for('autenticacao.gerenciar_documentos', id=usuario_id))

@bp_autenticacao.route('/usuarios/status/<int:id>')
@login_required
@cargo_exigido('rh_equipe') 
def alternar_status_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    if usuario.id == current_user.id:
        flash('Você não pode inativar seu próprio usuário.', 'error')
        return redirect(url_for('autenticacao.listar_usuarios'))
    usuario.ativo = not usuario.ativo
    db.session.commit()
    estado = "ativado" if usuario.ativo else "inativado"
    tipo_msg = "success" if usuario.ativo else "warning"
    flash(f'O usuário {usuario.nome} foi {estado} com sucesso.', tipo_msg)
    return redirect(url_for('autenticacao.listar_usuarios'))