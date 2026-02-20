from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from src.modulos.autenticacao.permissoes import cargo_exigido
from src.extensoes import banco_de_dados as db
from src.modulos.financeiro.modelos import Despesa, Fornecedor
from src.modulos.financeiro.formularios import FormularioDespesa
from src.modulos.autenticacao.modelos import Usuario
from src.modulos.rh.modelos import Colaborador
from . import bp_financeiro
from src.modulos.estoque.modelos import ProdutoEstoque, MovimentacaoEstoque
from decimal import Decimal

def add_months(source_date, months):
    return source_date + relativedelta(months=+months)

@bp_financeiro.route('/nova', methods=['GET', 'POST'])
@login_required
@cargo_exigido('financeiro_acesso')
def nova_despesa():
    form = FormularioDespesa()
    
    # 1. POPULA SELECTS
    form.fornecedor_id.choices = [(0, '--- Selecione (Opcional) ---')] + \
        [(f.id, f.nome_fantasia) for f in Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome_fantasia).all()]
    usuarios_db = Usuario.query.join(Colaborador).order_by(Colaborador.nome_completo).all()
    form.usuario_id.choices = [(0, '--- Selecione (Opcional) ---')] + [(u.id, u.nome) for u in usuarios_db]

    # Prepara produtos para o template (Select Oculto)
    produtos_disponiveis = ProdutoEstoque.query.filter_by(ativo=True).order_by(ProdutoEstoque.nome).all()

    if form.validate_on_submit():
        try:
            # === LÓGICA DE DADOS ===
            is_estoque = form.eh_compra_produto.data
            
            # Validação Condicional
            if not is_estoque and not form.descricao.data:
                form.descricao.errors.append('A descrição é obrigatória para despesas comuns.')
                return render_template('financeiro/nova_despesa.html', form=form, titulo="Nova Despesa", produtos_disponiveis=produtos_disponiveis)
            
            # --- CAPTURA DE LISTAS (Novo Fluxo) ---
            produtos_ids = request.form.getlist('produtos_ids[]')
            quantidades = request.form.getlist('quantidades[]')

            if is_estoque and not produtos_ids:
                flash('Adicione pelo menos um produto para compra de estoque.', 'error')
                return render_template('financeiro/nova_despesa.html', form=form, titulo="Nova Despesa", produtos_disponiveis=produtos_disponiveis)

            # Configurações de Parcelamento / Valor
            valor_total = form.valor.data
            tem_parcelamento = form.recorrente.data
            qtd_parcelas = form.qtd_repeticoes.data if tem_parcelamento else 1
            
            valor_parcela = valor_total
            desc_sulfixo = ""
            
            if is_estoque and qtd_parcelas > 1:
                valor_parcela = valor_total / qtd_parcelas
                desc_base = f"Compra Estoque ({len(produtos_ids)} itens)"
                categoria_final = 'material'
                tipo_custo_final = 'variavel'
            elif is_estoque: # 1 parcela
                desc_base = f"Compra Estoque ({len(produtos_ids)} itens)"
                categoria_final = 'material'
                tipo_custo_final = 'variavel'
            else: # Despesa Comum
                desc_base = form.descricao.data
                categoria_final = form.categoria.data
                tipo_custo_final = form.tipo_custo.data
            
            data_base_venc = form.data_vencimento.data
            data_base_compra = form.data_compra.data
            
            primeira_despesa_id = None # Para vincular estoque

            # LOOP FINANCEIRO
            for i in range(qtd_parcelas):
                nova_data_venc = add_months(data_base_venc, i)
                nova_data_comp = add_months(data_base_compra, i)
                
                desc_final = desc_base
                if qtd_parcelas > 1:
                    desc_final = f"{desc_base} - Parc. {i+1}/{qtd_parcelas}"
                
                status_final = form.status.data
                dt_pgto = form.data_pagamento.data
                
                if status_final == 'pago' and not dt_pgto: dt_pgto = date.today()
                
                # Apenas a 1ª parcela pode nascer paga se o usuário marcou
                if i > 0: 
                    status_final = 'pendente'
                    dt_pgto = None

                despesa = Despesa(
                    descricao=desc_final,
                    valor=valor_parcela,
                    data_vencimento=nova_data_venc,
                    data_competencia=nova_data_comp,
                    categoria=categoria_final,
                    tipo_custo=tipo_custo_final,
                    forma_pagamento=form.forma_pagamento.data,
                    status=status_final,
                    data_pagamento=dt_pgto,
                    codigo_barras=form.codigo_barras.data,
                    observacao=form.observacao.data
                )
                
                if form.fornecedor_id.data and form.fornecedor_id.data > 0:
                    despesa.fornecedor_id = form.fornecedor_id.data
                if form.usuario_id.data and form.usuario_id.data > 0:
                    despesa.usuario_id = form.usuario_id.data

                db.session.add(despesa)
                db.session.flush() # Gera ID
                
                if i == 0: primeira_despesa_id = despesa.id

            # LOOP ESTOQUE (Apenas se for compra de estoque e só 1 vez)
            if is_estoque and primeira_despesa_id:
                for p_id_str, qtd_str in zip(produtos_ids, quantidades):
                    if p_id_str and qtd_str:
                        prod = ProdutoEstoque.query.get(int(p_id_str))
                        qtd = Decimal(qtd_str)
                        
                        saldo_ant = prod.quantidade_atual
                        prod.quantidade_atual += qtd
                        
                        mov = MovimentacaoEstoque(
                            produto_id=prod.id,
                            tipo='entrada',
                            quantidade=qtd,
                            saldo_anterior=saldo_ant,
                            saldo_novo=prod.quantidade_atual,
                            origem='compra',
                            referencia_id=primeira_despesa_id, # Vincula à 1ª parcela
                            usuario_id=current_user.id,
                            observacao=f"Compra/Entrada em Lote (Ref: Despesa #{primeira_despesa_id})"
                        )
                        db.session.add(mov)

            db.session.commit()
            flash('Lançamento realizado com sucesso!', 'success')
            return redirect(url_for('financeiro.painel'))
            
        except Exception as e:
            db.session.rollback()
            print(f"ERRO: {e}")
            flash(f'Erro ao salvar: {str(e)}', 'error')

    return render_template('financeiro/nova_despesa.html', 
                           form=form, 
                           titulo="Nova Despesa", 
                           produtos_disponiveis=produtos_disponiveis)

@bp_financeiro.route('/editar/<int:id>', methods=['GET', 'POST'], endpoint='editar_despesa')
@login_required
@cargo_exigido('financeiro_acesso')
def editar_despesa(id):
    despesa = Despesa.query.get_or_404(id)
    form = FormularioDespesa(obj=despesa)
    
    # Verifica vínculo
    movimentacao = MovimentacaoEstoque.query.filter_by(referencia_id=despesa.id, origem='compra').first()
    eh_compra_estoque = (movimentacao is not None)

    colaborador_dados = None
    if despesa.colaborador_id:
        colaborador_dados = despesa.colaborador
    elif despesa.usuario_id:
        user = Usuario.query.get(despesa.usuario_id)
        if user and user.colaborador:
            colaborador_dados = user.colaborador

    form.fornecedor_id.choices = [(0, '--- Selecione (Opcional) ---')] + \
        [(f.id, f.nome_fantasia) for f in Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome_fantasia).all()]
    usuarios_db = Usuario.query.join(Colaborador).order_by(Colaborador.nome_completo).all()
    form.usuario_id.choices = [(0, '--- Selecione (Opcional) ---')] + [(u.id, u.nome) for u in usuarios_db]

    produtos_disponiveis = [] 

    if request.method == 'GET':
        if eh_compra_estoque:
            form.eh_compra_produto.data = True
        form.data_compra.data = despesa.data_competencia

    if form.validate_on_submit():
        despesa.descricao = form.descricao.data
        despesa.valor = form.valor.data
        despesa.data_vencimento = form.data_vencimento.data
        despesa.data_competencia = form.data_compra.data
        
        if not eh_compra_estoque:
            despesa.categoria = form.categoria.data
            despesa.tipo_custo = form.tipo_custo.data
        
        despesa.forma_pagamento = form.forma_pagamento.data
        despesa.status = form.status.data
        despesa.codigo_barras = form.codigo_barras.data
        despesa.observacao = form.observacao.data
        
        if form.status.data == 'pago':
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

    return render_template('financeiro/nova_despesa.html', 
                           form=form, 
                           titulo="Editar Lançamento", 
                           editando=True, 
                           eh_compra_estoque=eh_compra_estoque,
                           colaborador=colaborador_dados,
                           produtos_disponiveis=[])