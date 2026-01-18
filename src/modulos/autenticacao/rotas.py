from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from wtforms.validators import Optional
from src.extensoes import banco_de_dados as db
from src.modulos.autenticacao.modelos import Usuario, Modulo
from src.modulos.autenticacao.formularios import FormularioLogin, FormularioCadastroUsuario
from src.modulos.autenticacao.permissoes import cargo_exigido

bp_autenticacao = Blueprint('autenticacao', __name__, url_prefix='/auth')

# ... (Rotas de Login e Logout permanecem iguais) ...
@bp_autenticacao.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = FormularioLogin()
    if form.validate_on_submit():
        user_banco = Usuario.query.filter_by(usuario=form.usuario.data).first()
        if user_banco and user_banco.verificar_senha(form.senha.data):
            login_user(user_banco, remember=form.lembrar_de_mim.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Usuário ou senha incorretos.', 'error')
    return render_template('autenticacao/login.html', form=form)

@bp_autenticacao.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('autenticacao.login'))

# --- ROTAS DE GESTÃO ---

@bp_autenticacao.route('/usuarios', methods=['GET'])
@login_required
@cargo_exigido('rh_equipe') 
def listar_usuarios():
    usuarios = Usuario.query.all()
    return render_template('autenticacao/lista_usuarios.html', usuarios=usuarios)

@bp_autenticacao.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
@cargo_exigido('rh_equipe') 
def novo_usuario():
    form = FormularioCadastroUsuario()
    
    # --- 1. LÓGICA DE SEGURANÇA DE CARGOS ---
    # Define a lista completa de cargos e seus níveis (display, value, nivel_numerico)
    opcoes_cargos = [
        ('dono', 'Dono', 1),
        ('gerente', 'Gerente', 2),
        ('coordenador', 'Coordenador', 3),
        ('tecnico', 'Técnico', 4)
    ]
    
    # Filtra: Só mostre cargos onde o nível numérico é MAIOR ou IGUAL ao meu
    # (Lembre-se: 1 é o maior poder, 4 é o menor. Então se sou 2, só vejo 2, 3 e 4)
    cargos_permitidos = [
        (cargo_val, cargo_nome) 
        for cargo_val, cargo_nome, cargo_nivel in opcoes_cargos 
        if cargo_nivel >= current_user.nivel_acesso
    ]
    form.cargo.choices = cargos_permitidos

    # --- 2. LÓGICA DE SEGURANÇA DE MÓDULOS (PERMISSÕES) ---
    todos_modulos = Modulo.query.all()
    
    if current_user.cargo == 'dono':
        # Dono vê tudo e pode dar tudo
        form.modulos_acesso.choices = [(m.id, m.nome) for m in todos_modulos]
    else:
        # Outros só podem dar permissões que ELES MESMOS TÊM
        # Ex: Se eu não vejo Estoque, não posso dar acesso de Estoque para ninguém
        ids_meus_modulos = [m.id for m in current_user.permissoes]
        modulos_permitidos = [m for m in todos_modulos if m.id in ids_meus_modulos]
        form.modulos_acesso.choices = [(m.id, m.nome) for m in modulos_permitidos]

    # --- 3. LÓGICA DO SALÁRIO ---
    if current_user.cargo != 'dono' and not current_user.tem_permissao('rh_salarios'):
        del form.salario

    # --- PROCESSAMENTO DO FORMULÁRIO ---
    if form.validate_on_submit():
        # Verificação extra de segurança no Backend (Anti-Hack)
        # Garante que ele não injetou um valor de cargo via HTML
        nivel_novo_usuario = Usuario.NIVEIS_CARGO.get(form.cargo.data, 99)
        if nivel_novo_usuario < current_user.nivel_acesso:
             flash('Atenção: Você não pode criar um usuário com cargo superior ao seu.', 'error')
             return render_template('autenticacao/cadastro_usuario.html', form=form)

        if Usuario.query.filter_by(usuario=form.usuario.data).first():
            flash('Este usuário já existe.', 'error')
        else:
            novo_func = Usuario()
            novo_func.nome = form.nome.data
            novo_func.usuario = form.usuario.data
            novo_func.cpf = form.cpf.data
            novo_func.telefone = form.telefone.data
            novo_func.cargo = form.cargo.data
            novo_func.definir_senha(form.senha.data)
            
            if hasattr(form, 'salario') and form.salario.data:
                novo_func.salario = form.salario.data
            else:
                novo_func.salario = 0.0

            # Salva Permissões
            # Filtra novamente para garantir que só salvamos módulos que estavam nas opções permitidas
            ids_opcoes_validas = [choice[0] for choice in form.modulos_acesso.choices]
            ids_selecionados = [id_mod for id_mod in form.modulos_acesso.data if id_mod in ids_opcoes_validas]
            
            modulos_selecionados = Modulo.query.filter(Modulo.id.in_(ids_selecionados)).all()
            novo_func.permissoes = modulos_selecionados

            db.session.add(novo_func)
            db.session.commit()
            flash('Funcionário cadastrado com sucesso!', 'success')
            return redirect(url_for('autenticacao.listar_usuarios'))

    return render_template('autenticacao/cadastro_usuario.html', form=form)

# src/modulos/autenticacao/rotas.py

# ... (Mantenha as importações e outras rotas iguais) ...

@bp_autenticacao.route('/usuarios/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@cargo_exigido('rh_equipe') 
def editar_usuario(id):
    usuario_edit = Usuario.query.get_or_404(id)
    
    # Validação de Hierarquia
    if current_user.cargo != 'dono':
        if usuario_edit.nivel_acesso <= current_user.nivel_acesso and usuario_edit.id != current_user.id:
            flash('Você não tem permissão para editar este usuário.', 'error')
            return redirect(url_for('autenticacao.listar_usuarios'))

    form = FormularioCadastroUsuario(obj=usuario_edit)
    form.senha.validators = [Optional()] # Senha opcional na edição

    # Opções de Cargos e Módulos
    opcoes_cargos = [
        ('dono', 'Dono', 1),
        ('gerente', 'Gerente', 2),
        ('coordenador', 'Coordenador', 3),
        ('tecnico', 'Técnico', 4)
    ]
    cargos_permitidos = [
        (c_val, c_nome) for c_val, c_nome, c_lvl in opcoes_cargos 
        if c_lvl >= current_user.nivel_acesso
    ]
    form.cargo.choices = cargos_permitidos

    todos_modulos = Modulo.query.all()
    if current_user.cargo == 'dono':
        form.modulos_acesso.choices = [(m.id, m.nome) for m in todos_modulos]
    else:
        ids_meus = [m.id for m in current_user.permissoes]
        mods_permitidos = [m for m in todos_modulos if m.id in ids_meus]
        form.modulos_acesso.choices = [(m.id, m.nome) for m in mods_permitidos]

    if current_user.cargo != 'dono' and not current_user.tem_permissao('rh_salarios'):
        del form.salario

    # --- GET: Preencher o formulário ---
    if request.method == 'GET':
        form.modulos_acesso.data = [m.id for m in usuario_edit.permissoes]
        form.equipe.data = usuario_edit.equipe

    # --- POST: Salvar Alterações ---
    if form.validate_on_submit():
        # 1. VERIFICAÇÃO DE USUÁRIO DUPLICADO
        check_user = Usuario.query.filter(Usuario.usuario == form.usuario.data, Usuario.id != id).first()
        if check_user:
            flash(f'O usuário "{form.usuario.data}" já está em uso por outra pessoa.', 'error')
            return render_template('autenticacao/cadastro_usuario.html', form=form, editando=True)

        # 2. VERIFICAÇÃO DE CPF DUPLICADO (NOVA CORREÇÃO)
        if form.cpf.data:
            check_cpf = Usuario.query.filter(Usuario.cpf == form.cpf.data, Usuario.id != id).first()
            if check_cpf:
                flash(f'O CPF {form.cpf.data} já está cadastrado para o colaborador "{check_cpf.nome}".', 'error')
                return render_template('autenticacao/cadastro_usuario.html', form=form, editando=True)
        
        # 3. VERIFICAÇÃO DE E-MAIL DUPLICADO (NOVA CORREÇÃO)
        if form.email.data:
            check_email = Usuario.query.filter(Usuario.email == form.email.data, Usuario.id != id).first()
            if check_email:
                flash(f'O E-mail {form.email.data} já está em uso.', 'error')
                return render_template('autenticacao/cadastro_usuario.html', form=form, editando=True)

        # Atualiza campos básicos
        usuario_edit.nome = form.nome.data
        usuario_edit.usuario = form.usuario.data
        
        # Tratamento de campos opcionais únicos: Se vazio, salva como None (NULL no banco)
        # Isso evita erro de duplicidade se tiver dois usuários com string vazia ''
        usuario_edit.cpf = form.cpf.data if form.cpf.data else None
        usuario_edit.email = form.email.data if form.email.data else None
        
        usuario_edit.telefone = form.telefone.data
        usuario_edit.cargo = form.cargo.data
        usuario_edit.equipe = form.equipe.data
        
        if hasattr(form, 'salario'):
            usuario_edit.salario = form.salario.data

        if form.senha.data:
            usuario_edit.definir_senha(form.senha.data)

        # Atualiza Permissões
        ids_opcoes_validas = [c[0] for c in form.modulos_acesso.choices]
        ids_selecionados = [mid for mid in form.modulos_acesso.data if mid in ids_opcoes_validas]
        modulos_selecionados = Modulo.query.filter(Modulo.id.in_(ids_selecionados)).all()
        usuario_edit.permissoes = modulos_selecionados

        try:
            db.session.commit()
            flash('Dados atualizados com sucesso!', 'success')
            return redirect(url_for('autenticacao.listar_usuarios'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao salvar no banco de dados. Verifique os dados e tente novamente.', 'error')
            print(f"Erro DB: {e}") # Para debug no terminal

    return render_template('autenticacao/cadastro_usuario.html', form=form, editando=True)