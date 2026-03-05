from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from sqlalchemy import func, or_
from datetime import timedelta, datetime
from decimal import Decimal

from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import Venda, ItemVenda, Pagamento, hora_brasilia
from src.modulos.vendas.formularios import FormularioPagamento
from src.modulos.autenticacao.modelos import Usuario
from src.modulos.rh.modelos import Colaborador  # <--- IMPORTANTE: Adicionado para corrigir o erro

from src.modulos.autenticacao.permissoes import cargo_exigido

from . import bp_vendas

# Função para converter textos com vírgulas para formato de banco de dados
def converter_decimal(valor_str):
    if not valor_str: return Decimal('0.00')
    if isinstance(valor_str, (float, int, Decimal)): return Decimal(valor_str)
    
    valor_str = str(valor_str).strip()
    
    # Se contém vírgula, entende que é formato brasileiro (ex: 1.500,00) e limpa
    if ',' in valor_str:
        limpo = valor_str.replace('.', '').replace(',', '.')
    # Se não tem vírgula, já veio limpo/formato americano (ex: 1500.00)
    else:
        limpo = valor_str
        
    try: 
        return Decimal(limpo)
    except: 
        return Decimal('0.00')

# NOME PADRONIZADO: listar_vendas
@bp_vendas.route('/lista', methods=['GET'])
@login_required
@cargo_exigido('gestao_acesso')
def listar_vendas():
    # 1. Filtros
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    filtro_q = request.args.get('q', '').strip()
    filtro_status = request.args.get('status', '')
    filtro_vendedor = request.args.get('vendedor', '')
    filtro_data = request.args.get('data', '')

    # 2. Query
    query = Venda.query.filter(Venda.status != 'orcamento')

    if filtro_q:
        query = query.outerjoin(ItemVenda)
        condicoes = [
            Venda.cliente_nome.ilike(f'%{filtro_q}%'),
            Venda.descricao_servico.ilike(f'%{filtro_q}%'),
            ItemVenda.descricao.ilike(f'%{filtro_q}%'),
            Venda.cor_nome_snapshot.ilike(f'%{filtro_q}%')
        ]
        if filtro_q.isdigit():
            condicoes.append(Venda.id == int(filtro_q))
        query = query.filter(or_(*condicoes)).distinct()

    if filtro_status:
        query = query.filter(Venda.status == filtro_status)

    if filtro_vendedor:
        # CORREÇÃO: Join com Colaborador para filtrar pelo nome real
        query = query.join(Usuario, Venda.vendedor_id == Usuario.id)\
                     .join(Colaborador, Usuario.colaborador_id == Colaborador.id)\
                     .filter(Colaborador.nome_completo == filtro_vendedor)

    if filtro_data:
        query = query.filter(func.date(Venda.criado_em) == filtro_data)

    query = query.order_by(Venda.id.desc())
    paginacao = query.paginate(page=page, per_page=per_page, error_out=False)
    servicos = paginacao.items 
    
    # ==========================================
    # 3. KPIS
    # ==========================================
    hoje = hora_brasilia().date()
    inicio_mes = hoje.replace(day=1)
    data_30_dias_atras = hora_brasilia() - timedelta(days=30)
    
    total_vendido = db.session.query(func.sum(Venda.valor_final)).filter(Venda.status != 'orcamento', Venda.status != 'cancelado').scalar() or 0
    total_recebido_geral = db.session.query(func.sum(Pagamento.valor)).scalar() or 0
    
    a_receber = total_vendido - total_recebido_geral
    if a_receber < 0: a_receber = 0
    
    recebido_mes = db.session.query(func.sum(Pagamento.valor)).filter(Pagamento.data_pagamento >= inicio_mes).scalar() or 0
    
    # Contagens
    itens_pendente = ItemVenda.query.join(Venda).filter(ItemVenda.status=='pendente', Venda.status!='cancelado', Venda.modo=='multipla').count()
    itens_producao = ItemVenda.query.join(Venda).filter(ItemVenda.status=='producao', Venda.status!='cancelado', Venda.modo=='multipla').count()
    itens_pronto = ItemVenda.query.join(Venda).filter(ItemVenda.status=='pronto', Venda.status!='cancelado', Venda.modo=='multipla').count()
    
    vendas_simples_pendente = Venda.query.filter(Venda.modo == 'simples', Venda.status == 'pendente').count()
    vendas_simples_producao = Venda.query.filter(Venda.modo == 'simples', Venda.status == 'producao').count()
    vendas_simples_pronto = Venda.query.filter(Venda.modo == 'simples', Venda.status == 'pronto').count()
    
    qtd_pendente = itens_pendente + vendas_simples_pendente
    qtd_producao = itens_producao + vendas_simples_producao
    qtd_pronto = itens_pronto + vendas_simples_pronto
    
    qtd_cancelados_30d = Venda.query.filter(Venda.status == 'cancelado', Venda.data_cancelamento >= data_30_dias_atras).count()

    form_pgto = FormularioPagamento()
    
    # CORREÇÃO: Query para popular o Select de Vendedores (usando Colaborador)
    vendedores_query = db.session.query(Colaborador.nome_completo)\
        .join(Usuario, Usuario.colaborador_id == Colaborador.id)\
        .join(Venda, Venda.vendedor_id == Usuario.id)\
        .distinct().all()
        
    vendedores = [v[0] for v in vendedores_query]

    return render_template('vendas/gestao_servicos.html', 
                           servicos=servicos,
                           paginacao=paginacao,
                           vendedores=vendedores,
                           kpi_receber=a_receber,
                           kpi_recebido_mes=recebido_mes,
                           qtd_pendente=qtd_pendente,
                           qtd_producao=qtd_producao,
                           qtd_pronto=qtd_pronto,
                           qtd_cancelados=qtd_cancelados_30d,
                           form_pgto=form_pgto,
                           filtros={
                               'q': filtro_q,
                               'status': filtro_status,
                               'vendedor': filtro_vendedor,
                               'data': filtro_data
                           })

@bp_vendas.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@cargo_exigido('gestao_editar')
def editar_venda(id):
    venda = Venda.query.get_or_404(id)
    from src.modulos.estoque.modelos import ProdutoEstoque
    produtos_ativos = ProdutoEstoque.query.filter_by(ativo=True).order_by(ProdutoEstoque.nome).all()

    if request.method == 'POST':
        try:
            # 1. Dados do Cliente
            venda.tipo_cliente = request.form.get('tipo_cliente')
            if venda.tipo_cliente == 'PF':
                venda.cliente_nome = request.form.get('pf_nome')
                venda.cliente_documento = request.form.get('pf_cpf')
                venda.cliente_solicitante = None
            else:
                venda.cliente_nome = request.form.get('pj_fantasia')
                venda.cliente_documento = request.form.get('pj_cnpj')
                venda.cliente_solicitante = request.form.get('pj_solicitante')
            
            venda.cliente_contato = request.form.get('telefone')
            venda.cliente_email = request.form.get('email')
            venda.cliente_endereco = request.form.get('endereco')
            
            venda.prioridade = True if request.form.get('prioridade') == 'on' else False
            venda.descricao_servico = request.form.get('descricao_servico')
            venda.observacoes_internas = request.form.get('observacoes_internas')
            
            # 2. Financeiro Venda
            venda.valor_base = converter_decimal(request.form.get('valor_base'))
            venda.valor_acrescimo = converter_decimal(request.form.get('valor_acrescimo'))
            venda.tipo_desconto = request.form.get('tipo_desconto')
            venda.valor_desconto_aplicado = converter_decimal(request.form.get('valor_desconto_aplicado'))
            venda.valor_final = converter_decimal(request.form.get('valor_final'))
            
            # 3. Detalhes (Simples vs Múltiplo)
            if venda.modo == 'simples':
                venda.produto_id = int(request.form.get('produto_id')) if request.form.get('produto_id') else None
                venda.tipo_medida = request.form.get('tipo_medida')
                venda.dimensao_1 = converter_decimal(request.form.get('dimensao_1'))
                venda.dimensao_2 = converter_decimal(request.form.get('dimensao_2'))
                venda.dimensao_3 = converter_decimal(request.form.get('dimensao_3'))
                venda.quantidade_pecas = int(request.form.get('quantidade_pecas') or 1)
                venda.metragem_total = converter_decimal(request.form.get('metragem_total'))
                
                # Atualizar o item único
                if venda.itens:
                    item = venda.itens[0]
                    item.produto_id = venda.produto_id
                    item.quantidade = venda.quantidade_pecas
                    item.valor_total = venda.valor_final
                    item.descricao = venda.descricao_servico
            else:
                # Múltiplo - Atualizar Itens Dinamicamente
                itens_enviados_ids = []
                
                req_itens_id = request.form.getlist('itens_id[]')
                req_itens_desc = request.form.getlist('itens_descricao[]')
                req_itens_prod = request.form.getlist('itens_produto_id[]')
                req_itens_qtd = request.form.getlist('itens_qtd[]')
                req_itens_unit = request.form.getlist('itens_unit[]')
                req_itens_total = request.form.getlist('itens_total[]')
                
                for i in range(len(req_itens_desc)):
                    item_id_str = req_itens_id[i] if i < len(req_itens_id) else ""
                    desc = req_itens_desc[i]
                    prod_id = int(req_itens_prod[i]) if req_itens_prod[i] else None
                    qtd = converter_decimal(req_itens_qtd[i])
                    unit = converter_decimal(req_itens_unit[i])
                    total = converter_decimal(req_itens_total[i])
                    
                    if item_id_str and item_id_str != "novo":
                        item = ItemVenda.query.get(int(item_id_str))
                        if item and item.venda_id == venda.id:
                            item.descricao = desc
                            item.produto_id = prod_id
                            item.quantidade = qtd
                            item.valor_unitario = unit
                            item.valor_total = total
                            itens_enviados_ids.append(item.id)
                    else:
                        novo_item = ItemVenda(
                            venda_id=venda.id, descricao=desc, produto_id=prod_id,
                            quantidade=qtd, valor_unitario=unit, valor_total=total, status='pendente'
                        )
                        db.session.add(novo_item)
                        db.session.flush()
                        itens_enviados_ids.append(novo_item.id)
                        
                # Remove itens excluídos na interface
                for item in venda.itens:
                    if item.id not in itens_enviados_ids:
                        db.session.delete(item)
            
            # 4. Pagamentos
            pgtos_enviados_ids = []
            req_pgto_id = request.form.getlist('pgto_id[]')
            req_pgto_data = request.form.getlist('pgto_data[]')
            req_pgto_valor = request.form.getlist('pgto_valor[]')
            req_pgto_tipo = request.form.getlist('pgto_tipo[]')
            
            for i in range(len(req_pgto_data)):
                p_id_str = req_pgto_id[i] if i < len(req_pgto_id) else ""
                p_data_str = req_pgto_data[i]
                p_valor = converter_decimal(req_pgto_valor[i])
                p_tipo = req_pgto_tipo[i] if i < len(req_pgto_tipo) else "parcial"
                
                if not p_data_str or p_valor <= 0: continue
                    
                p_data = datetime.strptime(p_data_str, '%Y-%m-%d')
                
                if p_id_str and p_id_str != "novo":
                    pgto = Pagamento.query.get(int(p_id_str))
                    if pgto and pgto.venda_id == venda.id:
                        pgto.data_pagamento = p_data
                        pgto.valor = p_valor
                        pgto.tipo = p_tipo
                        pgtos_enviados_ids.append(pgto.id)
                else:
                    novo_pgto = Pagamento(
                        venda_id=venda.id, valor=p_valor, data_pagamento=p_data, tipo=p_tipo, usuario_id=current_user.id
                    )
                    db.session.add(novo_pgto)
                    db.session.flush()
                    pgtos_enviados_ids.append(novo_pgto.id)
                    
            for pgto in venda.pagamentos:
                if pgto.id not in pgtos_enviados_ids: db.session.delete(pgto)

            db.session.flush()
            if venda.valor_restante <= 0.01: venda.status_pagamento = 'pago'
            elif venda.valor_pago > 0: venda.status_pagamento = 'parcial'
            else: venda.status_pagamento = 'pendente'

            db.session.commit()
            flash('Serviço atualizado com sucesso!', 'success')
            return redirect(url_for('vendas.listar_vendas'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar serviço: {str(e)}', 'error')

    produtos_json = [{
        'id': p.id, 'nome': p.nome,
        'preco_m2': float(p.preco_m2) if p.preco_m2 else 0.0,
        'preco_m3': float(p.preco_m3) if p.preco_m3 else 0.0,
        'unidade_padrao': p.unidade
    } for p in produtos_ativos]

    return render_template('vendas/editar_venda.html', venda=venda, produtos_ativos=produtos_ativos, produtos_json=produtos_json)