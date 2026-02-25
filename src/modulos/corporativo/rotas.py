from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from sqlalchemy import func # <--- IMPORTANTE: Usado para checar maiúsculas/minúsculas
from src.extensoes import banco_de_dados as db
from src.modulos.autenticacao.permissoes import cargo_exigido
from src.modulos.corporativo.modelos import Setor, Cargo
from src.modulos.autenticacao.modelos import Modulo
from src.modulos.corporativo.formularios import FormularioSetor, FormularioCargo
from . import bp_corporativo

@bp_corporativo.route('/', methods=['GET', 'POST'])
@login_required
@cargo_exigido('rh_equipe') 
def painel():
    form_setor = FormularioSetor()
    form_cargo = FormularioCargo()
    
    # 1. Preenche Select de Setores
    setores_ativos = Setor.query.filter_by(ativo=True).order_by(Setor.nome).all()
    form_cargo.setor_id.choices = [(s.id, s.nome) for s in setores_ativos]
    if not form_cargo.setor_id.choices:
        form_cargo.setor_id.choices = [(0, 'Cadastre um setor primeiro')]

    # 2. Prepara Permissões (Para validação e agrupamento)
    todos_modulos = Modulo.query.order_by(Modulo.nome).all()
    form_cargo.permissoes.choices = [(m.id, m.nome) for m in todos_modulos]

    # --- LÓGICA DE AGRUPAMENTO (Para o Frontend) ---
    # === LÓGICA INTELIGENTE DE AGRUPAMENTO AUTOMÁTICO ===
    grupos_permissoes = {}
    
    # Busca os módulos já ordenados alfabeticamente
    todos_modulos = Modulo.query.order_by(Modulo.nome).all()
    
    for mod in todos_modulos:
        # Se o nome tiver " - ", ele usa a primeira palavra como o nome da pasta.
        # Exemplo: "Ponto de Venda - Criar" vira a pasta "Ponto de Venda"
        if " - " in mod.nome:
            nome_pasta = mod.nome.split(" - ")[0].strip()
        else:
            nome_pasta = "Administrativo" # Fallback caso alguma permissão não tenha o tracinho
            
        # Se a pasta ainda não existe no dicionário, cria ela
        if nome_pasta not in grupos_permissoes:
            grupos_permissoes[nome_pasta] = []
            
        # Adiciona a permissão dentro da pasta correta
        grupos_permissoes[nome_pasta].append(mod)

    # --- SALVAR NOVO SETOR ---
    if 'submit_setor' in request.form and form_setor.validate_on_submit():
        nome_setor = form_setor.nome.data.strip()
        
        # Validação: Verifica se o Setor já existe (Ignora maiúsculas/minúsculas)
        if Setor.query.filter(func.lower(Setor.nome) == func.lower(nome_setor)).first():
            flash(f'O setor "{nome_setor}" já está cadastrado no sistema.', 'error')
        else:
            novo_setor = Setor(nome=nome_setor, descricao=form_setor.descricao.data)
            db.session.add(novo_setor)
            db.session.commit()
            flash('Setor criado com sucesso!', 'success')
            
        return redirect(url_for('corporativo.painel'))

    # --- SALVAR NOVO CARGO ---
    if 'submit_cargo' in request.form and form_cargo.validate_on_submit():
        nome_cargo = form_cargo.nome.data.strip()
        
        # Validação: Verifica se o Cargo já existe (Ignora maiúsculas/minúsculas)
        if Cargo.query.filter(func.lower(Cargo.nome) == func.lower(nome_cargo)).first():
            flash(f'O cargo "{nome_cargo}" já está cadastrado no sistema.', 'error')
            return redirect(url_for('corporativo.painel'))

        novo_cargo = Cargo(
            nome=nome_cargo,
            setor_id=form_cargo.setor_id.data,
            nivel_hierarquico=form_cargo.nivel_hierarquico.data,
            descricao=form_cargo.descricao.data
        )
        
        ids_perms = form_cargo.permissoes.data
        if ids_perms:
            novo_cargo.permissoes = Modulo.query.filter(Modulo.id.in_(ids_perms)).all()

        db.session.add(novo_cargo)
        db.session.commit()
        flash('Cargo criado com permissões definidas!', 'success')
        return redirect(url_for('corporativo.painel'))

    # Listagens
    setores = Setor.query.order_by(Setor.nome).all()
    cargos = Cargo.query.join(Setor).order_by(Setor.nome, Cargo.nome).all()

    return render_template('corporativo/painel.html', 
                           form_setor=form_setor, 
                           form_cargo=form_cargo,
                           setores=setores,
                           cargos=cargos,
                           grupos_permissoes=grupos_permissoes)

# --- NOVA ROTA DE EDIÇÃO ---
@bp_corporativo.route('/cargo/editar/<int:id>', methods=['POST'])
@login_required
@cargo_exigido('rh_equipe')
def editar_cargo(id):
    cargo = Cargo.query.get_or_404(id)
    form = FormularioCargo()
    
    # Repopula choices para validar
    form.setor_id.choices = [(s.id, s.nome) for s in Setor.query.filter_by(ativo=True).all()]
    form.permissoes.choices = [(m.id, m.nome) for m in Modulo.query.all()]

    if form.validate_on_submit():
        nome_cargo = form.nome.data.strip()
        
        # Validação: Verifica se JÁ EXISTE OUTRO cargo com este nome (ignorando o próprio cargo editado)
        existente = Cargo.query.filter(func.lower(Cargo.nome) == func.lower(nome_cargo), Cargo.id != id).first()
        
        if existente:
            flash(f'Já existe outro cargo com o nome "{nome_cargo}".', 'error')
            return redirect(url_for('corporativo.painel'))
            
        cargo.nome = nome_cargo
        cargo.setor_id = form.setor_id.data
        cargo.nivel_hierarquico = form.nivel_hierarquico.data
        cargo.descricao = form.descricao.data
        
        # Atualiza Permissões
        ids_perms = form.permissoes.data
        if ids_perms:
            cargo.permissoes = Modulo.query.filter(Modulo.id.in_(ids_perms)).all()
        else:
            cargo.permissoes = []

        db.session.commit()
        flash('Cargo atualizado com sucesso!', 'success')
    else:
        flash('Erro ao atualizar cargo. Verifique os campos.', 'error')
        
    return redirect(url_for('corporativo.painel'))

# --- NOVA ROTA DE EXCLUSÃO DE CARGO ---
@bp_corporativo.route('/cargo/excluir/<int:id>', methods=['GET'])
@login_required
@cargo_exigido('rh_equipe')
def excluir_cargo(id):
    from src.modulos.rh.modelos import Colaborador # Import local para evitar referência circular
    
    cargo = Cargo.query.get_or_404(id)
    
    # 1. Validação de Segurança: Bloqueia se houver pessoas usando este cargo
    colaboradores_vinculados = Colaborador.query.filter_by(cargo_id=id).count()
    if colaboradores_vinculados > 0:
        flash(f'Ação bloqueada! O cargo "{cargo.nome}" não pode ser excluído porque possui {colaboradores_vinculados} colaborador(es) vinculado(s) a ele. Altere o cargo deles primeiro no módulo de RH.', 'error')
        return redirect(url_for('corporativo.painel'))
    
    # 2. Desvincula as permissões (Limpa a tabela intermediária)
    cargo.permissoes = []
    
    # 3. Deleta o cargo
    db.session.delete(cargo)
    db.session.commit()
    
    flash(f'Cargo "{cargo.nome}" excluído com sucesso.', 'success')
    return redirect(url_for('corporativo.painel'))