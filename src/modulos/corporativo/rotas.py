from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from src.extensoes import banco_de_dados as db
from src.modulos.autenticacao.permissoes import cargo_exigido
from src.modulos.corporativo.modelos import Setor, Cargo
from src.modulos.corporativo.formularios import FormularioSetor, FormularioCargo
from . import bp_corporativo

@bp_corporativo.route('/', methods=['GET', 'POST'])
@login_required
@cargo_exigido('rh_equipe') # Permissão compartilhada com RH
def painel():
    # Instancia os formulários
    form_setor = FormularioSetor()
    form_cargo = FormularioCargo()
    
    # Preenche o select de setores no formulário de cargo
    setores_ativos = Setor.query.filter_by(ativo=True).order_by(Setor.nome).all()
    form_cargo.setor_id.choices = [(s.id, s.nome) for s in setores_ativos]
    
    # Se não houver setores, adiciona opção vazia para não quebrar o form
    if not form_cargo.setor_id.choices:
        form_cargo.setor_id.choices = [(0, 'Cadastre um setor primeiro')]

    # LÓGICA: Salvar Novo Setor
    if 'submit_setor' in request.form and form_setor.validate_on_submit():
        novo_setor = Setor(
            nome=form_setor.nome.data, 
            descricao=form_setor.descricao.data
        )
        db.session.add(novo_setor)
        db.session.commit()
        flash('Setor criado com sucesso!', 'success')
        return redirect(url_for('corporativo.painel'))

    # LÓGICA: Salvar Novo Cargo
    if 'submit_cargo' in request.form and form_cargo.validate_on_submit():
        novo_cargo = Cargo(
            nome=form_cargo.nome.data,
            setor_id=form_cargo.setor_id.data,
            nivel_hierarquico=form_cargo.nivel_hierarquico.data,
            descricao=form_cargo.descricao.data
        )
        db.session.add(novo_cargo)
        db.session.commit()
        flash('Cargo criado com sucesso!', 'success')
        return redirect(url_for('corporativo.painel'))

    # Listagens para as tabelas
    setores = Setor.query.order_by(Setor.nome).all()
    cargos = Cargo.query.join(Setor).order_by(Setor.nome, Cargo.nome).all()

    return render_template('corporativo/painel.html', 
                           form_setor=form_setor, 
                           form_cargo=form_cargo,
                           setores=setores,
                           cargos=cargos)