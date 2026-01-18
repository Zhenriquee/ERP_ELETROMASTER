from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from src.extensoes import banco_de_dados as db
from src.modulos.financeiro.modelos import Despesa, Fornecedor
from src.modulos.financeiro.formularios import FormularioDespesa
from src.modulos.autenticacao.modelos import Usuario
from . import bp_financeiro

def add_months(source_date, months):
    return source_date + relativedelta(months=+months)

@bp_financeiro.route('/nova', methods=['GET', 'POST'])
@login_required
def nova_despesa():
    form = FormularioDespesa()
    
    # Popula selects
    form.fornecedor_id.choices = [(0, '--- Selecione (Opcional) ---')] + \
        [(f.id, f.nome_fantasia) for f in Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome_fantasia).all()]
    form.usuario_id.choices = [(0, '--- Selecione (Opcional) ---')] + \
        [(u.id, u.nome) for u in Usuario.query.order_by(Usuario.nome).all()]

    if form.validate_on_submit():
        # Lógica de Recorrência
        repeticoes = 1
        if form.recorrente.data and form.qtd_repeticoes.data:
            repeticoes = form.qtd_repeticoes.data

        # Tratamento da Competência
        comp_str = form.data_competencia.data 
        try:
            data_comp_base = datetime.strptime(comp_str + '-01', '%Y-%m-%d').date()
        except ValueError:
            data_comp_base = date.today()

        for i in range(repeticoes):
            nova_data_vencimento = add_months(form.data_vencimento.data, i)
            nova_data_competencia = add_months(data_comp_base, i)
            
            descricao_final = form.descricao.data
            if repeticoes > 1:
                descricao_final = f"{form.descricao.data} ({i+1}/{repeticoes})"
            
            status_final = form.status.data
            data_pgto_final = form.data_pagamento.data # Pega do formulário se preenchido
            
            # Se status for pago e não tiver data, define hoje
            if status_final == 'pago' and not data_pgto_final:
                data_pgto_final = date.today()
            
            # Recorrência futura sempre nasce pendente
            if i > 0: 
                status_final = 'pendente'
                data_pgto_final = None

            despesa = Despesa(
                descricao=descricao_final,
                valor=form.valor.data,
                data_vencimento=nova_data_vencimento,
                data_competencia=nova_data_competencia,
                categoria=form.categoria.data,
                tipo_custo=form.tipo_custo.data,
                forma_pagamento=form.forma_pagamento.data,
                status=status_final,
                data_pagamento=data_pgto_final, # Salva a data correta
                codigo_barras=form.codigo_barras.data,
                observacao=form.observacao.data
            )
            
            if form.fornecedor_id.data and form.fornecedor_id.data > 0:
                despesa.fornecedor_id = form.fornecedor_id.data
            if form.usuario_id.data and form.usuario_id.data > 0:
                despesa.usuario_id = form.usuario_id.data

            db.session.add(despesa)

        db.session.commit()
        msg = 'Despesa lançada com sucesso!' if repeticoes == 1 else f'{repeticoes} despesas lançadas!'
        flash(msg, 'success')
        return redirect(url_for('financeiro.painel'))

    return render_template('financeiro/nova_despesa.html', form=form, titulo="Nova Despesa")

# --- NOVA ROTA: EDITAR / VER DETALHES ---
@bp_financeiro.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_despesa(id):
    despesa = Despesa.query.get_or_404(id)
    form = FormularioDespesa(obj=despesa)
    
    # Popula selects
    form.fornecedor_id.choices = [(0, '--- Selecione (Opcional) ---')] + \
        [(f.id, f.nome_fantasia) for f in Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome_fantasia).all()]
    form.usuario_id.choices = [(0, '--- Selecione (Opcional) ---')] + \
        [(u.id, u.nome) for u in Usuario.query.order_by(Usuario.nome).all()]

    if request.method == 'GET':
        # Preenche o campo de competência (date -> string YYYY-MM)
        if despesa.data_competencia:
            form.data_competencia.data = despesa.data_competencia.strftime('%Y-%m')

    if form.validate_on_submit():
        # Tratamento da Competência
        comp_str = form.data_competencia.data
        try:
            nova_comp = datetime.strptime(comp_str + '-01', '%Y-%m-%d').date()
        except:
            nova_comp = despesa.data_competencia

        despesa.descricao = form.descricao.data
        despesa.valor = form.valor.data
        despesa.data_vencimento = form.data_vencimento.data
        despesa.data_competencia = nova_comp
        despesa.categoria = form.categoria.data
        despesa.tipo_custo = form.tipo_custo.data
        despesa.forma_pagamento = form.forma_pagamento.data
        despesa.status = form.status.data
        despesa.codigo_barras = form.codigo_barras.data
        despesa.observacao = form.observacao.data
        
        # Lógica Data Pagamento
        if form.status.data == 'pago':
            # Se o usuário informou uma data, usa ela. Se não, usa hoje.
            if form.data_pagamento.data:
                despesa.data_pagamento = form.data_pagamento.data
            elif not despesa.data_pagamento:
                despesa.data_pagamento = date.today()
        else:
            despesa.data_pagamento = None

        despesa.fornecedor_id = form.fornecedor_id.data if form.fornecedor_id.data > 0 else None
        despesa.usuario_id = form.usuario_id.data if form.usuario_id.data > 0 else None

        db.session.commit()
        flash('Despesa atualizada com sucesso!', 'success')
        return redirect(url_for('financeiro.painel'))

    return render_template('financeiro/nova_despesa.html', form=form, titulo="Detalhes da Despesa", editando=True)