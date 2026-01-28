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

# ... imports ...

# FUNÇÃO AUXILIAR PARA AGRUPAR MÓDULOS
def agrupar_modulos(todos_modulos):
    grupos = {
        'Dashboard (Tela Inicial)': [],
        'Gestão de Vendas & Serviços': [],
        'Módulos Operacionais': [],
        'Administrativo & Financeiro': []
    }
    
    for m in todos_modulos:
        if m.codigo.startswith('dash_'):
            grupos['Dashboard (Tela Inicial)'].append(m)
        elif m.codigo.startswith('vendas_'):
            grupos['Gestão de Vendas & Serviços'].append(m)
        elif m.codigo in ['producao_operar', 'estoque_gerir', 'produtos_gerir']:
            grupos['Módulos Operacionais'].append(m)
        else:
            grupos['Administrativo & Financeiro'].append(m)
            
    return grupos

# --- ROTA NOVO USUÁRIO ---
@bp_autenticacao.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
@cargo_exigido('rh_equipe') 
def novo_usuario():
    form = FormularioCadastroUsuario()
    
    # Opções de Cargo
    opcoes_cargos = [('dono', 'Dono', 1), ('gerente', 'Gerente', 2), ('coordenador', 'Coordenador', 3), ('tecnico', 'Técnico', 4)]
    form.cargo.choices = [(v, n) for v, n, l in opcoes_cargos if l >= current_user.nivel_acesso]

    # Carrega Módulos
    todos_modulos = Modulo.query.order_by(Modulo.nome).all()
    
    # Filtra se não for dono
    if current_user.cargo != 'dono':
        ids_meus = [m.id for m in current_user.permissoes]
        todos_modulos = [m for m in todos_modulos if m.id in ids_meus]

    # Preenche o SelectMultiple do WTForms para validação
    form.modulos_acesso.choices = [(m.id, m.nome) for m in todos_modulos]

    # AGRUPA PARA O TEMPLATE
    modulos_grupos = {
        'Dashboard': [m for m in todos_modulos if m.codigo.startswith('dash_')],
        'Vendas': [m for m in todos_modulos if m.codigo.startswith('vendas_')],
        'Gestão': [m for m in todos_modulos if m.codigo in ['producao_operar', 'estoque_gerir', 'produtos_gerir', 'metas_equipe']],
        'Admin': [m for m in todos_modulos if m.codigo in ['financeiro_acesso', 'rh_equipe', 'rh_salarios']]
    }

    if current_user.cargo != 'dono' and not current_user.tem_permissao('rh_salarios'):
        del form.salario

    if form.validate_on_submit():
        # ... (Validações de nível e existência de usuário mantidas iguais) ...
        if Usuario.query.filter_by(usuario=form.usuario.data).first():
            flash('Este usuário já existe.', 'error')
        else:
            novo_func = Usuario()
            # ... (Preenchimento dos dados básicos mantido igual) ...
            novo_func.nome = form.nome.data
            novo_func.usuario = form.usuario.data
            novo_func.cpf = form.cpf.data
            novo_func.telefone = form.telefone.data
            novo_func.cargo = form.cargo.data
            novo_func.equipe = form.equipe.data
            novo_func.ativo = form.ativo.data
            novo_func.definir_senha(form.senha.data)
            
            if hasattr(form, 'salario'): novo_func.salario = form.salario.data

            # Salva Permissões
            ids_selecionados = form.modulos_acesso.data
            novo_func.permissoes = Modulo.query.filter(Modulo.id.in_(ids_selecionados)).all()

            db.session.add(novo_func)
            db.session.commit()
            flash('Funcionário cadastrado!', 'success')
            return redirect(url_for('autenticacao.listar_usuarios'))

    return render_template('autenticacao/cadastro_usuario.html', form=form, modulos_grupos=modulos_grupos)

# --- ROTA EDITAR USUÁRIO ---
# ... (Mantenha os imports e a função novo_usuario iguais) ...

@bp_autenticacao.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
# Removemos a exigência estrita de 'rh_equipe' aqui para permitir que o usuário edite o PRÓPRIO perfil
# A verificação de segurança será feita manualmente dentro da função
def editar_usuario(id):
    usuario_edit = Usuario.query.get_or_404(id)
    
    # === REGRA 1: USUÁRIO SÓ EDITA A SI MESMO (EXCETO DONO) ===
    if current_user.cargo != 'dono':
        if current_user.id != usuario_edit.id:
            flash('Você não tem permissão para editar outros usuários.', 'error')
            return redirect(url_for('autenticacao.listar_usuarios'))

    form = FormularioCadastroUsuario(obj=usuario_edit)
    form.senha.validators = [Optional()]

    # Opções de Cargo
    opcoes_cargos = [('dono', 'Dono', 1), ('gerente', 'Gerente', 2), ('coordenador', 'Coordenador', 3), ('tecnico', 'Técnico', 4)]
    
    # === REGRA 2: APENAS DONO PODE MUDAR CARGO ===
    if current_user.cargo == 'dono':
        # Dono vê todas as opções permitidas pela hierarquia
        form.cargo.choices = [(v, n) for v, n, l in opcoes_cargos]
    else:
        # Usuário comum: A lista de opções contém APENAS o cargo atual dele
        # Isso garante que a validação do formulário passe, mas ele não tem opção de troca
        form.cargo.choices = [(usuario_edit.cargo, usuario_edit.cargo.title())]

    # Carrega Módulos
    todos_modulos = Modulo.query.order_by(Modulo.nome).all()
    if current_user.cargo != 'dono':
        ids_meus = [m.id for m in current_user.permissoes]
        todos_modulos = [m for m in todos_modulos if m.id in ids_meus]

    form.modulos_acesso.choices = [(m.id, m.nome) for m in todos_modulos]

    # Agrupamento para o Template
    modulos_grupos = {
        'Dashboard': [m for m in todos_modulos if m.codigo.startswith('dash_')],
        'Vendas': [m for m in todos_modulos if m.codigo.startswith('vendas_')],
        'Gestão': [m for m in todos_modulos if m.codigo in ['producao_operar', 'estoque_gerir', 'produtos_gerir', 'metas_equipe']],
        'Admin': [m for m in todos_modulos if m.codigo in ['financeiro_acesso', 'rh_equipe', 'rh_salarios']]
    }

    # Salário só Dono ou RH vê
    if current_user.cargo != 'dono' and not current_user.tem_permissao('rh_salarios'):
        del form.salario

    if request.method == 'GET':
        form.modulos_acesso.data = [m.id for m in usuario_edit.permissoes]
        form.ativo.data = usuario_edit.ativo

    if form.validate_on_submit():
        # Validações de duplicidade (Login/CPF/Email)
        check_user = Usuario.query.filter(Usuario.usuario == form.usuario.data, Usuario.id != id).first()
        if check_user:
            flash(f'O usuário "{form.usuario.data}" já está em uso.', 'error')
            return render_template('autenticacao/cadastro_usuario.html', form=form, editando=True, modulos_grupos=modulos_grupos)

        # Atualiza dados básicos
        usuario_edit.nome = form.nome.data
        usuario_edit.usuario = form.usuario.data
        usuario_edit.cpf = form.cpf.data if form.cpf.data else None
        usuario_edit.email = form.email.data if form.email.data else None
        usuario_edit.telefone = form.telefone.data
        usuario_edit.equipe = form.equipe.data
        
        # === APLICAÇÃO DA REGRA 2 NO BANCO ===
        # Só atualiza o cargo se quem está editando for o DONO
        if current_user.cargo == 'dono':
            usuario_edit.cargo = form.cargo.data
            usuario_edit.ativo = form.ativo.data # Só dono (ou RH autorizado) pode inativar, aqui deixamos aberto ao dono
        # Se não for dono, mantemos o cargo e status que já estava no objeto usuario_edit
        
        if hasattr(form, 'salario'): usuario_edit.salario = form.salario.data
        if form.senha.data: usuario_edit.definir_senha(form.senha.data)

        # Atualiza Permissões
        # Se o usuário não for dono, ele só pode atribuir permissões que ele mesmo tem (filtrado no GET acima)
        usuario_edit.permissoes = Modulo.query.filter(Modulo.id.in_(form.modulos_acesso.data)).all()
        
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
        
        # Se editou o próprio perfil, volta para o dashboard
        if current_user.id == usuario_edit.id:
             return redirect(url_for('dashboard.painel'))
             
        return redirect(url_for('autenticacao.listar_usuarios'))

    return render_template('autenticacao/cadastro_usuario.html', form=form, editando=True, modulos_grupos=modulos_grupos)

@bp_autenticacao.route('/usuarios/<int:id>/documentos', methods=['GET', 'POST'])
@login_required
@cargo_exigido('rh_equipe')
def gerenciar_documentos(id):
    usuario_alvo = Usuario.query.get_or_404(id)
    form = FormularioDocumento()
    
    # Verifica/Cria pasta de upload
    upload_path = current_app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_path):
        os.makedirs(upload_path)

    if form.validate_on_submit():
        arquivo = form.arquivo.data
        filename_original = secure_filename(arquivo.filename)
        extensao = filename_original.rsplit('.', 1)[1].lower() if '.' in filename_original else ''
        
        # Gera nome único: ID_USUARIO_TIMESTAMP.ext
        novo_nome = f"{usuario_alvo.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{extensao}"
        
        # Salva no disco
        caminho_completo = os.path.join(upload_path, novo_nome)
        arquivo.save(caminho_completo)
        
        # Calcula tamanho em KB
        tamanho = os.path.getsize(caminho_completo) / 1024

        # Salva no banco
        doc = DocumentoUsuario(
            usuario_id=usuario_alvo.id,
            nome_arquivo=novo_nome,
            nome_original=form.descricao.data, # Usamos a descrição como nome visível
            tipo_arquivo=extensao,
            tamanho_kb=tamanho,
            enviado_por_id=current_user.id
        )
        db.session.add(doc)
        db.session.commit()
        
        flash('Documento anexado com sucesso!', 'success')
        return redirect(url_for('autenticacao.gerenciar_documentos', id=usuario_alvo.id))

    documentos = DocumentoUsuario.query.filter_by(usuario_id=usuario_alvo.id).order_by(DocumentoUsuario.criado_em.desc()).all()
    
    return render_template('autenticacao/documentos.html', 
                           usuario=usuario_alvo, 
                           form=form, 
                           documentos=documentos)

@bp_autenticacao.route('/documentos/baixar/<int:doc_id>')
@login_required
@cargo_exigido('rh_equipe')
def baixar_documento(doc_id):
    doc = DocumentoUsuario.query.get_or_404(doc_id)
    path = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(path, doc.nome_arquivo, as_attachment=True, download_name=f"{doc.nome_original}.{doc.tipo_arquivo}")

@bp_autenticacao.route('/documentos/deletar/<int:doc_id>')
@login_required
@cargo_exigido('rh_equipe')
def deletar_documento(doc_id):
    doc = DocumentoUsuario.query.get_or_404(doc_id)
    usuario_id = doc.usuario_id
    
    try:
        # Remove do disco
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], doc.nome_arquivo)
        if os.path.exists(path):
            os.remove(path)
            
        # Remove do banco
        db.session.delete(doc)
        db.session.commit()
        flash('Documento removido.', 'success')
    except Exception as e:
        flash(f'Erro ao deletar: {str(e)}', 'error')
        
    return redirect(url_for('autenticacao.gerenciar_documentos', id=usuario_id))

# src/modulos/autenticacao/rotas/usuarios.py

# ... (rota baixar_documento existente) ...

@bp_autenticacao.route('/documentos/visualizar/<int:doc_id>')
@login_required
@cargo_exigido('rh_equipe')
def visualizar_documento(doc_id):
    """
    Rota para pré-visualização inline (no navegador).
    Diferente do 'baixar', esta rota não força o download (as_attachment=False).
    """
    doc = DocumentoUsuario.query.get_or_404(doc_id)
    path = current_app.config['UPLOAD_FOLDER']
    
    # O Flask detecta automaticamente o Content-Type baseado na extensão do arquivo.
    # as_attachment=False diz ao navegador para tentar exibir o arquivo se puder.
    return send_from_directory(path, doc.nome_arquivo, as_attachment=False)

# ... (rota deletar_documento existente) ...

@bp_autenticacao.route('/usuarios/status/<int:id>')
@login_required
@cargo_exigido('rh_equipe') 
def alternar_status_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    
    # Proteção para não inativar a si mesmo
    if usuario.id == current_user.id:
        flash('Você não pode inativar seu próprio usuário.', 'error')
        return redirect(url_for('autenticacao.listar_usuarios'))
    
    # Alterna o status
    usuario.ativo = not usuario.ativo
    db.session.commit()
    
    estado = "ativado" if usuario.ativo else "inativado"
    tipo_msg = "success" if usuario.ativo else "warning"
    
    flash(f'O usuário {usuario.nome} foi {estado} com sucesso.', tipo_msg)
    return redirect(url_for('autenticacao.listar_usuarios'))