from flask import render_template
from flask_login import login_required
from sqlalchemy import func, extract, and_
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import Venda, Pagamento
from src.modulos.financeiro.modelos import Despesa
from src.modulos.metas.modelos import MetaMensal
from src.modulos.dashboard import bp_dashboard

def fmt_moeda(valor):
    if not valor: return "0,00"
    return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@bp_dashboard.route('/')
@login_required
def painel():
    hoje = date.today()
    mes_atual = hoje.month
    ano_atual = hoje.year

    # --- 1. ENTRADAS (REALIZADO) & PREVISÃO ---
    # AJUSTE 1: Valor RECEBIDO no mês (Soma dos pagamentos efetivados)
    recebido_mes = db.session.query(func.sum(Pagamento.valor))\
        .filter(extract('month', Pagamento.data_pagamento) == mes_atual, 
                extract('year', Pagamento.data_pagamento) == ano_atual)\
        .scalar() or 0

    # Total a Receber (Geral)
    total_vendido_geral = db.session.query(func.sum(Venda.valor_final)).filter(Venda.status != 'cancelada', Venda.status != 'orcamento').scalar() or 0
    total_pago_geral = db.session.query(func.sum(Pagamento.valor)).scalar() or 0
    a_receber = total_vendido_geral - total_pago_geral
    if a_receber < 0: a_receber = 0

    # --- 2. META DIÁRIA ---
    meta_config = MetaMensal.query.filter_by(mes=mes_atual, ano=ano_atual).first()
    meta_valor_mes = float(meta_config.valor_loja) if meta_config else 1
    dias_uteis = meta_config.dias_uteis if meta_config and meta_config.dias_uteis > 0 else 1
    meta_diaria_alvo = meta_valor_mes / dias_uteis

    vendas_hoje = db.session.query(func.sum(Venda.valor_final))\
        .filter(func.date(Venda.criado_em) == hoje,
                Venda.status != 'cancelada', Venda.status != 'orcamento').scalar() or 0
    
    atingimento_dia_perc = (float(vendas_hoje) / meta_diaria_alvo) * 100 if meta_diaria_alvo > 0 else 0

    # --- 3. A PAGAR (Mês Atual) ---
    a_pagar_mes = db.session.query(func.sum(Despesa.valor))\
        .filter(extract('month', Despesa.data_vencimento) == mes_atual,
                extract('year', Despesa.data_vencimento) == ano_atual,
                Despesa.status == 'pendente').scalar() or 0

    # --- 4. ALERTAS DE VENCIMENTO (DETALHADO) ---
    # AJUSTE 2: Buscamos a LISTA COMPLETA para exibir no modal
    
    # Lista de Vencidos (Data < Hoje)
    lista_vencidos = Despesa.query.filter(
        Despesa.status == 'pendente',
        Despesa.data_vencimento < hoje
    ).order_by(Despesa.data_vencimento.asc()).all()
                
    # Lista de Próximos (Hoje <= Data <= Hoje + 5 dias)
    limite_aviso = hoje + timedelta(days=5)
    lista_proximos = Despesa.query.filter(
        Despesa.status == 'pendente',
        Despesa.data_vencimento >= hoje,
        Despesa.data_vencimento <= limite_aviso
    ).order_by(Despesa.data_vencimento.asc()).all()

    # Contagens para o Card
    qtd_vencidos = len(lista_vencidos)
    qtd_proximos = len(lista_proximos)

    # --- GRÁFICOS (Mantidos) ---
    chart_labels = []
    chart_data_receitas = [] # Agora usamos recebimentos no gráfico também? Ou mantemos vendas? Vamos manter Vendas no gráfico de fluxo para ver competência.
    chart_data_vendas = []
    chart_data_despesas = []

    for i in range(5, -1, -1):
        data_ref = hoje - relativedelta(months=i)
        mes_iter = data_ref.month
        ano_iter = data_ref.year
        nome_mes = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez'][mes_iter-1]
        chart_labels.append(nome_mes)

        soma_v = db.session.query(func.sum(Venda.valor_final))\
            .filter(extract('month', Venda.criado_em) == mes_iter, 
                    extract('year', Venda.criado_em) == ano_iter,
                    Venda.status != 'cancelada', Venda.status != 'orcamento').scalar() or 0
        chart_data_vendas.append(float(soma_v))

        soma_d = db.session.query(func.sum(Despesa.valor))\
            .filter(extract('month', Despesa.data_competencia) == mes_iter, 
                    extract('year', Despesa.data_competencia) == ano_iter).scalar() or 0
        chart_data_despesas.append(float(soma_d))

    # Gráfico Rosca
    cats_db = db.session.query(Despesa.categoria, func.sum(Despesa.valor))\
        .filter(extract('month', Despesa.data_competencia) == mes_atual,
                extract('year', Despesa.data_competencia) == ano_atual)\
        .group_by(Despesa.categoria).all()
    
    doughnut_labels = [c[0].title() for c in cats_db]
    doughnut_data = [float(c[1]) for c in cats_db]
    
    if not doughnut_data:
        status_db = db.session.query(Venda.status, func.count(Venda.id))\
            .filter(extract('month', Venda.criado_em) == mes_atual)\
            .group_by(Venda.status).all()
        doughnut_labels = [s[0].upper() for s in status_db]
        doughnut_data = [int(s[1]) for s in status_db]

    # Meta Progresso Mês (Baseado em Faturamento ou Recebimento? Normalmente Meta é Venda)
    # Vamos manter Meta sobre Venda para não confundir o comercial
    faturamento_mes = db.session.query(func.sum(Venda.valor_final))\
        .filter(extract('month', Venda.criado_em) == mes_atual, 
                extract('year', Venda.criado_em) == ano_atual,
                Venda.status != 'cancelada', Venda.status != 'orcamento').scalar() or 0
                
    perc_meta_mes = (float(faturamento_mes) / meta_valor_mes) * 100

    return render_template('dashboard/painel.html',
                           # KPI 1: RECEBIDO + A Receber
                           kpi_recebido=fmt_moeda(recebido_mes), # Mudou de Faturamento para Recebido
                           kpi_receber=fmt_moeda(a_receber),
                           
                           # KPI 2: Meta
                           vendas_hoje=fmt_moeda(vendas_hoje),
                           meta_diaria_alvo=fmt_moeda(meta_diaria_alvo),
                           atingimento_dia_perc=round(atingimento_dia_perc, 1),
                           
                           # KPI 3: A Pagar
                           kpi_pagar=fmt_moeda(a_pagar_mes),
                           
                           # KPI 4: Listas e Contagens
                           qtd_vencidos=qtd_vencidos,
                           qtd_proximos=qtd_proximos,
                           lista_vencidos=lista_vencidos, # Passamos a lista
                           lista_proximos=lista_proximos, # Passamos a lista
                           
                           # Gráficos
                           chart_labels=chart_labels,
                           chart_vendas=chart_data_vendas,
                           chart_despesas=chart_data_despesas,
                           doughnut_labels=doughnut_labels,
                           doughnut_data=doughnut_data,
                           meta_valor=fmt_moeda(meta_valor_mes),
                           perc_meta=round(perc_meta_mes, 1),
                           fmt_moeda=fmt_moeda) # Passamos a função para formatar dentro do modal