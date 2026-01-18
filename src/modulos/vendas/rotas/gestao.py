from flask import render_template, request
from flask_login import login_required
from sqlalchemy import func
from datetime import timedelta

# Importa o banco e modelos
from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import Venda, ItemVenda, Pagamento, hora_brasilia
from src.modulos.vendas.formularios import FormularioPagamento

# Importa o Blueprint da pasta atual (o arquivo __init__.py)
from . import bp_vendas

@bp_vendas.route('/servicos', methods=['GET'])
@login_required
def gestao_servicos():
    # ==========================================
    # 1. PAGINAÇÃO E ORDENAÇÃO
    # ==========================================
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Itens por página
    
    # Filtra (ignora orçamentos) e Ordena (ID decrescente: mais novo no topo)
    query = Venda.query.filter(Venda.status != 'orcamento').order_by(Venda.id.desc())
    
    # Executa a paginação
    paginacao = query.paginate(page=page, per_page=per_page, error_out=False)
    servicos = paginacao.items # Lista de vendas da página atual
    
    # ==========================================
    # 2. KPIS FINANCEIROS
    # ==========================================
    hoje = hora_brasilia().date()
    inicio_mes = hoje.replace(day=1)
    data_30_dias_atras = hora_brasilia() - timedelta(days=30)
    
    total_vendido = db.session.query(func.sum(Venda.valor_final)).filter(Venda.status != 'orcamento', Venda.status != 'cancelado').scalar() or 0
    total_recebido_geral = db.session.query(func.sum(Pagamento.valor)).scalar() or 0
    
    a_receber = total_vendido - total_recebido_geral
    if a_receber < 0: a_receber = 0
    
    recebido_mes = db.session.query(func.sum(Pagamento.valor)).filter(Pagamento.data_pagamento >= inicio_mes).scalar() or 0
    
    # ==========================================
    # 3. KPIS OPERACIONAIS (SINCRONIZADOS COM PRODUÇÃO)
    # ==========================================
    # Lógica: Soma (Itens de Vendas Múltiplas) + (Vendas Simples)
    # Exclui vendas canceladas para não inflar os números.
    
    # A) Contagem de Itens Individuais (Venda Múltipla)
    itens_pendente = ItemVenda.query.filter_by(status='pendente').join(Venda).filter(Venda.status != 'cancelado').count()
    itens_producao = ItemVenda.query.filter_by(status='producao').join(Venda).filter(Venda.status != 'cancelado').count()
    itens_pronto = ItemVenda.query.filter_by(status='pronto').join(Venda).filter(Venda.status != 'cancelado').count()
    
    # B) Contagem de Vendas Simples (Sem itens na tabela ItemVenda)
    vendas_simples_pendente = Venda.query.filter(Venda.modo == 'simples', Venda.status == 'pendente').count()
    vendas_simples_producao = Venda.query.filter(Venda.modo == 'simples', Venda.status == 'producao').count()
    vendas_simples_pronto = Venda.query.filter(Venda.modo == 'simples', Venda.status == 'pronto').count()
    
    # C) Totais Unificados (Números dos cards coloridos)
    qtd_pendente = itens_pendente + vendas_simples_pendente
    qtd_producao = itens_producao + vendas_simples_producao
    qtd_pronto = itens_pronto + vendas_simples_pronto
    
    # D) Cancelados (apenas Vendas nos últimos 30 dias)
    qtd_cancelados_30d = Venda.query.filter(
        Venda.status == 'cancelado',
        Venda.data_cancelamento >= data_30_dias_atras
    ).count()

    # ==========================================
    # 4. DADOS AUXILIARES
    # ==========================================
    form_pgto = FormularioPagamento()
    
    # Filtro de vendedores presentes na lista atual
    vendedores = set(s.vendedor.nome for s in servicos)

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
                           form_pgto=form_pgto)