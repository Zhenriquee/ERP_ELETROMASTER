from flask import render_template, request
from flask_login import login_required
from sqlalchemy import func, or_
from datetime import timedelta

from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import Venda, ItemVenda, Pagamento, hora_brasilia
from src.modulos.vendas.formularios import FormularioPagamento
from src.modulos.autenticacao.modelos import Usuario

from . import bp_vendas

# NOME PADRONIZADO: listar_vendas
@bp_vendas.route('/lista', methods=['GET'])
@login_required
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
        query = query.join(Usuario, Venda.vendedor_id == Usuario.id).filter(Usuario.nome == filtro_vendedor)

    if filtro_data:
        query = query.filter(func.date(Venda.criado_em) == filtro_data)

    query = query.order_by(Venda.id.desc())
    paginacao = query.paginate(page=page, per_page=per_page, error_out=False)
    servicos = paginacao.items 
    
    # ==========================================
    # 3. KPIS (CORRIGIDO)
    # ==========================================
    hoje = hora_brasilia().date()
    inicio_mes = hoje.replace(day=1)
    data_30_dias_atras = hora_brasilia() - timedelta(days=30)
    
    total_vendido = db.session.query(func.sum(Venda.valor_final)).filter(Venda.status != 'orcamento', Venda.status != 'cancelado').scalar() or 0
    total_recebido_geral = db.session.query(func.sum(Pagamento.valor)).scalar() or 0
    
    a_receber = total_vendido - total_recebido_geral
    if a_receber < 0: a_receber = 0
    
    recebido_mes = db.session.query(func.sum(Pagamento.valor)).filter(Pagamento.data_pagamento >= inicio_mes).scalar() or 0
    
    # --- LÓGICA CORRIGIDA: Separação estrita entre Multipla (Itens) e Simples (Venda) ---
    
    # 1. Contagem de Itens (Apenas de Vendas Múltiplas)
    itens_pendente = ItemVenda.query.join(Venda).filter(ItemVenda.status=='pendente', Venda.status!='cancelado', Venda.modo=='multipla').count()
    itens_producao = ItemVenda.query.join(Venda).filter(ItemVenda.status=='producao', Venda.status!='cancelado', Venda.modo=='multipla').count()
    itens_pronto = ItemVenda.query.join(Venda).filter(ItemVenda.status=='pronto', Venda.status!='cancelado', Venda.modo=='multipla').count()
    
    # 2. Contagem de Vendas Simples (Pelo status da Venda Pai)
    vendas_simples_pendente = Venda.query.filter(Venda.modo == 'simples', Venda.status == 'pendente').count()
    vendas_simples_producao = Venda.query.filter(Venda.modo == 'simples', Venda.status == 'producao').count()
    vendas_simples_pronto = Venda.query.filter(Venda.modo == 'simples', Venda.status == 'pronto').count()
    
    # 3. Soma
    qtd_pendente = itens_pendente + vendas_simples_pendente
    qtd_producao = itens_producao + vendas_simples_producao
    qtd_pronto = itens_pronto + vendas_simples_pronto
    
    qtd_cancelados_30d = Venda.query.filter(Venda.status == 'cancelado', Venda.data_cancelamento >= data_30_dias_atras).count()

    form_pgto = FormularioPagamento()
    
    vendedores_query = db.session.query(Usuario.nome).join(Venda, Venda.vendedor_id == Usuario.id).distinct().all()
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