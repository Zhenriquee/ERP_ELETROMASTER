from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from src.extensoes import banco_de_dados as db
from src.modulos.autenticacao.permissoes import cargo_exigido

# Imports dos Modelos
from src.modulos.rh.modelos import Colaborador
# Importamos Cargo para preencher o Select (Assumindo que o arquivo já existe ou será criado)
from src.modulos.corporativo.modelos import Cargo 

from src.modulos.rh.formularios import FormularioColaborador
from . import bp_rh

# --- LISTAGEM DE COLABORADORES ---
@bp_rh.route('/', methods=['GET'])
@login_required
@cargo_exigido('rh_equipe')
def listar_colaboradores():
    colaboradores = Colaborador.query.order_by(Colaborador.ativo.desc(), Colaborador.nome_completo).all()
    return render_template('rh/lista_colaboradores.html', colaboradores=colaboradores)

# --- NOVO COLABORADOR ---
@bp_rh.route('/novo', methods=['GET', 'POST'])
@login_required
@cargo_exigido('rh_equipe')
def novo_colaborador():
    form = FormularioColaborador()
    
    # Popula o Select de Cargos
    cargos_db = Cargo.query.filter_by(ativo=True).order_by(Cargo.nome).all()
    form.cargo_id.choices = [(c.id, f"{c.nome} - {c.setor.nome}") for c in cargos_db]
    
    # Se não houver cargos, adiciona opção vazia para não quebrar
    if not form.cargo_id.choices:
        form.cargo_id.choices = [(0, 'Nenhum cargo cadastrado')]

    if form.validate_on_submit():
        # Verifica CPF duplicado
        if Colaborador.query.filter_by(cpf=form.cpf.data).first():
            flash('Este CPF já está cadastrado.', 'error')
        else:
            novo = Colaborador(
                nome_completo=form.nome_completo.data,
                cpf=form.cpf.data,
                rg=form.rg.data,
                data_nascimento=form.data_nascimento.data,
                email_pessoal=form.email_pessoal.data,
                telefone=form.telefone.data,
                endereco=form.endereco.data,
                cargo_id=form.cargo_id.data,
                data_admissao=form.data_admissao.data,
                tipo_contrato=form.tipo_contrato.data,
                salario_base=form.salario_base.data,
                ativo=form.ativo.data
            )
            db.session.add(novo)
            db.session.commit()
            flash('Colaborador cadastrado com sucesso!', 'success')
            return redirect(url_for('rh.listar_colaboradores'))

    return render_template('rh/cadastro_colaborador.html', form=form, titulo="Novo Colaborador")

# --- EDITAR COLABORADOR ---
@bp_rh.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@cargo_exigido('rh_equipe')
def editar_colaborador(id):
    colab = Colaborador.query.get_or_404(id)
    form = FormularioColaborador(obj=colab)
    
    # Popula Cargos
    cargos_db = Cargo.query.order_by(Cargo.nome).all()
    form.cargo_id.choices = [(c.id, f"{c.nome} - {c.setor.nome}") for c in cargos_db]

    if form.validate_on_submit():
        # Verifica CPF duplicado (excluindo o próprio)
        existente = Colaborador.query.filter(Colaborador.cpf == form.cpf.data, Colaborador.id != id).first()
        if existente:
            flash('Este CPF já pertence a outro colaborador.', 'error')
        else:
            form.populate_obj(colab) # Atualiza o objeto com os dados do form
            db.session.commit()
            flash('Dados atualizados com sucesso.', 'success')
            return redirect(url_for('rh.listar_colaboradores'))

    return render_template('rh/cadastro_colaborador.html', form=form, titulo="Editar Colaborador", editando=True)

# --- DETALHES / PERFIL ---
@bp_rh.route('/perfil/<int:id>')
@login_required
@cargo_exigido('rh_equipe')
def perfil_colaborador(id):
    colab = Colaborador.query.get_or_404(id)
    return render_template('rh/perfil_colaborador.html', colab=colab)