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
import uuid

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
            # GERA O CÓDIGO DO GRUPO SE FOR PARCELADO
            grupo_id = str(uuid.uuid4()) if qtd_parcelas > 1 else None

            # LOOP FINANCEIRO
            for i in range(qtd_parcelas):
                nova_data_venc = add_months(data_base_venc, i)
                nova_data_comp = add_months(data_base_compra, i)
                
                desc_final = desc_base
                
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
                    observacao=form.observacao.data,
                    grupo_parcelamento=grupo_id 
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
    
    # 1. Busca movimentações antigas atreladas a esta despesa
    movimentacoes_antigas = MovimentacaoEstoque.query.filter_by(referencia_id=despesa.id, origem='compra').all()
    eh_compra_estoque = len(movimentacoes_antigas) > 0

    colaborador_dados = None
    if despesa.colaborador_id: colaborador_dados = despesa.colaborador
    elif despesa.usuario_id:
        user = Usuario.query.get(despesa.usuario_id)
        if user and user.colaborador: colaborador_dados = user.colaborador

    form.fornecedor_id.choices = [(0, '--- Selecione (Opcional) ---')] + [(f.id, f.nome_fantasia) for f in Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome_fantasia).all()]
    usuarios_db = Usuario.query.join(Colaborador).order_by(Colaborador.nome_completo).all()
    form.usuario_id.choices = [(0, '--- Selecione (Opcional) ---')] + [(u.id, u.nome) for u in usuarios_db]

    produtos_disponiveis = ProdutoEstoque.query.filter_by(ativo=True).order_by(ProdutoEstoque.nome).all()
    itens_salvos = [{'produto_id': m.produto_id, 'quantidade': float(m.quantidade)} for m in movimentacoes_antigas]

    if request.method == 'GET':
        if eh_compra_estoque: form.eh_compra_produto.data = True
        form.data_compra.data = despesa.data_competencia
        
        # Recupera as parcelas
        if despesa.grupo_parcelamento:
            qtd_parcelas = Despesa.query.filter_by(grupo_parcelamento=despesa.grupo_parcelamento).count()
            if qtd_parcelas > 1:
                form.recorrente.data = True
                form.qtd_repeticoes.data = qtd_parcelas
                form.descricao.data = despesa.descricao.split(' - Parc.')[0].strip()
                
                # --- NOVO PONTO 1 (VISUALIZAÇÃO) ---
                # Se é estoque e estava parcelado, o banco guarda o valor unitário.
                # Multiplicamos pela quantidade para que a tela mostre o TOTAL da nota corretamente (ex: 1000).
                if eh_compra_estoque:
                    form.valor.data = despesa.valor * qtd_parcelas

    if form.validate_on_submit():
        desc_base = form.descricao.data.split(' - Parc.')[0].strip()
        
        # --- NOVO PONTO 1 (MATEMÁTICA E REDISTRIBUIÇÃO) ---
        nova_qtd = form.qtd_repeticoes.data if form.recorrente.data else 1
        is_estoque = form.eh_compra_produto.data
        
        valor_parcela = form.valor.data
        # Se for estoque e tiver parcelamento, recorta o "Total" lido da tela e divide pela nova quantidade
        if is_estoque and nova_qtd > 1:
            valor_parcela = form.valor.data / nova_qtd

        despesa.descricao = desc_base
        despesa.valor = valor_parcela # Salva o valor matematicamente correto para a conta atual
        despesa.data_vencimento = form.data_vencimento.data
        despesa.data_competencia = form.data_compra.data
        
        if not form.eh_compra_produto.data:
            despesa.categoria = form.categoria.data
            despesa.tipo_custo = form.tipo_custo.data
        
        despesa.forma_pagamento = form.forma_pagamento.data
        despesa.status = form.status.data
        despesa.codigo_barras = form.codigo_barras.data
        despesa.observacao = form.observacao.data
        
        if form.status.data == 'pago':
            if form.data_pagamento.data: despesa.data_pagamento = form.data_pagamento.data
            elif not despesa.data_pagamento: despesa.data_pagamento = date.today()
        else: despesa.data_pagamento = None

        despesa.fornecedor_id = form.fornecedor_id.data if form.fornecedor_id.data > 0 else None
        despesa.usuario_id = form.usuario_id.data if form.usuario_id.data > 0 else None

        # --- 4. ATUALIZAÇÃO DO ESTOQUE (ESTORNO E RE-ENTRADA) ---
        # Este é o bloco que garante que o seu 2º Ponto funcione perfeitamente!
        if is_estoque:
            produtos_ids = request.form.getlist('produtos_ids[]')
            quantidades = request.form.getlist('quantidades[]')

            for mov in movimentacoes_antigas:
                prod = ProdutoEstoque.query.get(mov.produto_id)
                if prod: prod.quantidade_atual -= mov.quantidade
                db.session.delete(mov)
            db.session.flush()

            for p_id_str, qtd_str in zip(produtos_ids, quantidades):
                if p_id_str and qtd_str:
                    prod = ProdutoEstoque.query.get(int(p_id_str))
                    qtd = Decimal(str(qtd_str).replace(',', '.'))
                    
                    saldo_ant = prod.quantidade_atual
                    prod.quantidade_atual += qtd
                    
                    nova_mov = MovimentacaoEstoque(
                        produto_id=prod.id, tipo='entrada', quantidade=qtd,
                        saldo_anterior=saldo_ant, saldo_novo=prod.quantidade_atual, origem='compra',
                        referencia_id=despesa.id, usuario_id=current_user.id, observacao=f"Compra Editada (Ref: Despesa #{despesa.id})"
                    )
                    db.session.add(nova_mov)
                    
        elif eh_compra_estoque and not is_estoque:
            for mov in movimentacoes_antigas:
                prod = ProdutoEstoque.query.get(mov.produto_id)
                if prod: prod.quantidade_atual -= mov.quantidade
                db.session.delete(mov)

        # --- 5. ATUALIZAÇÃO DAS PARCELAS ---
        import uuid
        
        if despesa.grupo_parcelamento:
            grupo_id = despesa.grupo_parcelamento
            todas_parcelas = Despesa.query.filter_by(grupo_parcelamento=grupo_id).order_by(Despesa.data_vencimento.asc()).all()
            qtd_atual = len(todas_parcelas)
            parcelas_ativas = todas_parcelas.copy()
            
            if nova_qtd > qtd_atual:
                ultima = todas_parcelas[-1]
                for i in range(1, nova_qtd - qtd_atual + 1):
                    nova = Despesa(
                        descricao=desc_base,
                        valor=valor_parcela, # Salva o valor recalculado na nova parcela
                        data_vencimento=add_months(ultima.data_vencimento, i), data_competencia=add_months(ultima.data_competencia, i),
                        categoria=despesa.categoria, tipo_custo=despesa.tipo_custo, forma_pagamento=despesa.forma_pagamento, status='pendente', fornecedor_id=despesa.fornecedor_id, usuario_id=despesa.usuario_id, grupo_parcelamento=grupo_id, observacao=despesa.observacao
                    )
                    db.session.add(nova)
                    parcelas_ativas.append(nova)
                    
            elif nova_qtd < qtd_atual:
                parcelas_para_deletar = todas_parcelas[nova_qtd:]
                for p in parcelas_para_deletar:
                    if p.id != despesa.id: db.session.delete(p)
                parcelas_ativas = todas_parcelas[:nova_qtd]
                
            for p in parcelas_ativas:
                p.descricao = desc_base
                p.valor = valor_parcela # ATUALIZA O VALOR DE TODAS AS PARCELAS IRMÃS 
                        
        else:
            if form.recorrente.data and nova_qtd > 1:
                grupo_id = str(uuid.uuid4())
                despesa.grupo_parcelamento = grupo_id
                despesa.descricao = desc_base
                for i in range(1, nova_qtd):
                    nova = Despesa(
                        descricao=desc_base,
                        valor=valor_parcela, # Salva o valor recalculado na nova parcela
                        data_vencimento=add_months(despesa.data_vencimento, i), data_competencia=add_months(despesa.data_competencia, i), categoria=despesa.categoria, tipo_custo=despesa.tipo_custo, forma_pagamento=despesa.forma_pagamento, status='pendente', fornecedor_id=despesa.fornecedor_id, usuario_id=despesa.usuario_id, grupo_parcelamento=grupo_id, observacao=despesa.observacao
                    )
                    db.session.add(nova)

        db.session.commit()
        flash('Despesa e estoque atualizados com sucesso!', 'success')
        return redirect(url_for('financeiro.painel'))

    return render_template('financeiro/nova_despesa.html', 
                           form=form, 
                           titulo="Editar Lançamento", 
                           editando=True, 
                           eh_compra_estoque=eh_compra_estoque, 
                           colaborador=colaborador_dados, 
                           produtos_disponiveis=produtos_disponiveis, 
                           itens_salvos=itens_salvos)