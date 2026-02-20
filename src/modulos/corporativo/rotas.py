from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
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
    grupos_permissoes = {
        'Dashboard': [],
        'Vendas': [],
        'Financeiro': [],
        'Estoque': [],
        'Operacional': [],
        'Metas': [],
        'Relatórios': [], # <--- NOVA CATEGORIA ADICIONADA AQUI
        'Administrativo': []
    }

    for m in todos_modulos:
        cod = m.codigo.lower()
        if cod.startswith('dash_'): grupos_permissoes['Dashboard'].append(m)
        elif cod.startswith('vendas_'): grupos_permissoes['Vendas'].append(m)
        elif cod.startswith('financeiro_'): grupos_permissoes['Financeiro'].append(m)
        elif cod.startswith('estoque_'): grupos_permissoes['Estoque'].append(m)
        elif cod.startswith('producao_'): grupos_permissoes['Operacional'].append(m)
        elif cod.startswith('metas_'): grupos_permissoes['Metas'].append(m)
        elif cod.startswith('relatorios_'): grupos_permissoes['Relatórios'].append(m) # <--- CAPTURA O NOVO MÓDULO
        elif cod.startswith('rh_'): grupos_permissoes['Administrativo'].append(m)
        else: grupos_permissoes['Administrativo'].append(m)
    
    # Remove grupos vazios
    grupos_permissoes = {k: v for k, v in grupos_permissoes.items() if v}

    # --- SALVAR NOVO SETOR ---
    if 'submit_setor' in request.form and form_setor.validate_on_submit():
        novo_setor = Setor(nome=form_setor.nome.data, descricao=form_setor.descricao.data)
        db.session.add(novo_setor)
        db.session.commit()
        flash('Setor criado com sucesso!', 'success')
        return redirect(url_for('corporativo.painel'))

    # --- SALVAR NOVO CARGO ---
    if 'submit_cargo' in request.form and form_cargo.validate_on_submit():
        novo_cargo = Cargo(
            nome=form_cargo.nome.data,
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
                           grupos_permissoes=grupos_permissoes) # Passamos os grupos

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
        cargo.nome = form.nome.data
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