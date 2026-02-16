from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from src.modulos.autenticacao.permissoes import cargo_exigido # Importante
from src.extensoes import banco_de_dados as db
from src.modulos.financeiro.modelos import Despesa, Fornecedor
from src.modulos.financeiro.formularios import FormularioDespesa
from src.modulos.autenticacao.modelos import Usuario
from src.modulos.rh.modelos import Colaborador # Import necessário para o Join
from . import bp_financeiro
from src.modulos.estoque.modelos import ProdutoEstoque, MovimentacaoEstoque

def add_months(source_date, months):
    return source_date + relativedelta(months=+months)

@bp_financeiro.route('/nova', methods=['GET', 'POST'])
@login_required
@cargo_exigido('financeiro_acesso')
def nova_despesa():
    form = FormularioDespesa()
    
    # 1. POPULA SELECTS (Mantido)
    form.fornecedor_id.choices = [(0, '--- Selecione (Opcional) ---')] + \
        [(f.id, f.nome_fantasia) for f in Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome_fantasia).all()]
    # CORREÇÃO DA QUERY DE USUÁRIOS (Evita o erro de Property)
    usuarios_db = Usuario.query.join(Colaborador).order_by(Colaborador.nome_completo).all()
    form.usuario_id.choices = [(0, '--- Selecione (Opcional) ---')] + [(u.id, u.nome) for u in usuarios_db]

    try:
        produtos = ProdutoEstoque.query.filter_by(ativo=True).order_by(ProdutoEstoque.nome).all()
        form.produto_estoque_id.choices = [(0, '--- Selecione o Produto ---')] + [(p.id, f"{p.nome} ({p.unidade})") for p in produtos]
    except:
        form.produto_estoque_id.choices = [(0, 'Erro ao carregar produtos')]

    if form.validate_on_submit():
        try:
            # === VALIDAÇÃO CONDICIONAL ===
            if not form.eh_compra_produto.data and not form.descricao.data:
                form.descricao.errors.append('A descrição é obrigatória para despesas comuns.')
                return render_template('financeiro/nova_despesa.html', form=form, titulo="Nova Despesa")

            if form.eh_compra_produto.data:
                if not form.produto_estoque_id.data or form.produto_estoque_id.data == 0:
                    form.produto_estoque_id.errors.append('Selecione um produto para continuar.')
                    return render_template('financeiro/nova_despesa.html', form=form, titulo="Nova Despesa")
            # =============================

            # 1. Configura Nome e Recorrência baseado no tipo
            if form.eh_compra_produto.data:
                # Regra 1 e 2: Descrição automática e Sem Recorrência
                prod = ProdutoEstoque.query.get(form.produto_estoque_id.data)
                descricao_final = f"Compra Estoque: {prod.nome}"
                
                # Força recorrência desligada para produtos
                repeticoes = 1
                
                # Força categoria e tipo
                categoria_final = 'material'
                tipo_custo_final = 'variavel'
            else:
                descricao_final = form.descricao.data
                repeticoes = form.qtd_repeticoes.data if (form.recorrente.data and form.qtd_repeticoes.data) else 1
                categoria_final = form.categoria.data
                tipo_custo_final = form.tipo_custo.data

            data_base_vencimento = form.data_vencimento.data
            
            # Loop de Salvamento (Ajustado)
            for i in range(repeticoes):
                nova_data_vencimento = add_months(data_base_vencimento, i)
                nova_data_competencia = nova_data_vencimento.replace(day=1)
                
                desc_parcela = descricao_final
                if repeticoes > 1:
                    desc_parcela = f"{descricao_final} ({i+1}/{repeticoes})"
                
                # Status e Pagamento
                status_final = form.status.data
                data_pgto_final = form.data_pagamento.data
                
                if status_final == 'pago' and not data_pgto_final:
                    data_pgto_final = date.today()
                
                if i > 0: 
                    status_final = 'pendente'
                    data_pgto_final = None

                despesa = Despesa(
                    descricao=desc_parcela,
                    valor=form.valor.data,
                    data_vencimento=nova_data_vencimento,
                    data_competencia=nova_data_competencia,
                    categoria=categoria_final,
                    tipo_custo=tipo_custo_final,
                    forma_pagamento=form.forma_pagamento.data,
                    status=status_final,
                    data_pagamento=data_pgto_final,
                    codigo_barras=form.codigo_barras.data,
                    observacao=form.observacao.data
                )
                
                if form.fornecedor_id.data and form.fornecedor_id.data > 0:
                    despesa.fornecedor_id = form.fornecedor_id.data
                if form.usuario_id.data and form.usuario_id.data > 0:
                    despesa.usuario_id = form.usuario_id.data

                db.session.add(despesa)
                db.session.flush()

                # Movimentação de Estoque (Apenas se for produto e apenas 1 vez)
                if form.eh_compra_produto.data and i == 0:
                    prod_id = form.produto_estoque_id.data
                    qtd = form.qtd_estoque.data
                    
                    if prod_id and qtd:
                        produto = ProdutoEstoque.query.get(prod_id)
                        saldo_anterior = produto.quantidade_atual
                        produto.quantidade_atual += qtd
                        
                        mov = MovimentacaoEstoque(
                            produto_id=produto.id,
                            tipo='entrada',
                            quantidade=qtd,
                            saldo_anterior=saldo_anterior,
                            saldo_novo=produto.quantidade_atual,
                            origem='compra',
                            referencia_id=despesa.id,
                            usuario_id=current_user.id,
                            observacao=f"Compra Financeiro #{despesa.id}"
                        )
                        db.session.add(mov)

            db.session.commit()
            flash('Lançamento realizado com sucesso!', 'success')
            return redirect(url_for('financeiro.painel'))
            
        except Exception as e:
            db.session.rollback()
            print(f"ERRO: {e}")
            flash(f'Erro ao salvar: {str(e)}', 'error')

    return render_template('financeiro/nova_despesa.html', form=form, titulo="Nova Despesa")


@bp_financeiro.route('/editar/<int:id>', methods=['GET', 'POST'], endpoint='editar_despesa')
@login_required
@cargo_exigido('financeiro_acesso')
def editar_despesa(id):
    despesa = Despesa.query.get_or_404(id)
    form = FormularioDespesa(obj=despesa)
    
    # Verifica vínculo com estoque
    movimentacao = MovimentacaoEstoque.query.filter_by(referencia_id=despesa.id, origem='compra').first()
    eh_compra_estoque = (movimentacao is not None)

    # Verifica vínculo com Colaborador (Para o template)
    colaborador_dados = None
    if despesa.colaborador_id:
        colaborador_dados = despesa.colaborador
    elif despesa.usuario_id:
        user = Usuario.query.get(despesa.usuario_id)
        if user and user.colaborador:
            colaborador_dados = user.colaborador

    # POPULA SELECTS (CORRIGIDO AQUI TAMBÉM)
    form.fornecedor_id.choices = [(0, '--- Selecione (Opcional) ---')] + \
        [(f.id, f.nome_fantasia) for f in Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome_fantasia).all()]
    
    # CORREÇÃO DO ERRO DE ORDENAÇÃO
    usuarios_db = Usuario.query.join(Colaborador).order_by(Colaborador.nome_completo).all()
    form.usuario_id.choices = [(0, '--- Selecione (Opcional) ---')] + [(u.id, u.nome) for u in usuarios_db]
    
    # Produtos
    try:
        produtos = ProdutoEstoque.query.filter_by(ativo=True).order_by(ProdutoEstoque.nome).all()
        form.produto_estoque_id.choices = [(0, '--- Selecione ---')] + [(p.id, f"{p.nome}") for p in produtos]
    except: form.produto_estoque_id.choices = [(0, 'Erro')]

    if request.method == 'GET':
        if eh_compra_estoque:
            form.eh_compra_produto.data = True
            form.produto_estoque_id.data = movimentacao.produto_id
            form.qtd_estoque.data = movimentacao.quantidade

    if form.validate_on_submit():
        despesa.descricao = form.descricao.data
        despesa.valor = form.valor.data
        despesa.data_vencimento = form.data_vencimento.data
        despesa.data_competencia = despesa.data_vencimento.replace(day=1)
        
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

    # Importante: Passar 'colaborador' (português) para o template
    return render_template('financeiro/nova_despesa.html', 
                           form=form, 
                           titulo="Editar Lançamento", 
                           editando=True, 
                           eh_compra_estoque=eh_compra_estoque,
                           colaborador=colaborador_dados)