from flask import render_template
from flask_login import login_required, current_user # Adicione current_user se não tiver
from sqlalchemy import func, extract, desc
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import Venda, Pagamento, ItemVenda, CorServico
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

    # --- VERIFICAÇÃO DE PERMISSÃO ---
    # Só exibe dados financeiros se for Dono ou tiver permissão no módulo Financeiro
    exibir_financeiro = current_user.cargo == 'dono' or current_user.tem_permissao('financeiro_acesso')

    # Inicializa variáveis financeiras com 0 ou vazio caso não tenha acesso
    recebido_mes = 0
    a_receber = 0
    vendas_hoje = 0
    meta_diaria_alvo = 0
    atingimento_dia_perc = 0
    a_pagar_mes = 0
    qtd_vencidos = 0
    qtd_proximos = 0
    lista_vencidos = []
    lista_proximos = []
    ticket_medio = 0
    meta_valor_mes = 0
    perc_meta_mes = 0
    
    chart_labels = []
    chart_data_vendas = []
    chart_data_despesas = []
    doughnut_labels = []
    doughnut_data = []

    # === BLOCO FINANCEIRO (SÓ EXECUTA SE TIVER PERMISSÃO) ===
    if exibir_financeiro:
        # 1. ENTRADAS & PREVISÃO
        recebido_mes = db.session.query(func.sum(Pagamento.valor))\
            .filter(extract('month', Pagamento.data_pagamento) == mes_atual, 
                    extract('year', Pagamento.data_pagamento) == ano_atual).scalar() or 0

        total_vendido_geral = db.session.query(func.sum(Venda.valor_final)).filter(Venda.status != 'cancelada', Venda.status != 'orcamento').scalar() or 0
        total_pago_geral = db.session.query(func.sum(Pagamento.valor)).scalar() or 0
        a_receber = total_vendido_geral - total_pago_geral
        if a_receber < 0: a_receber = 0

        # 2. META DIÁRIA
        meta_config = MetaMensal.query.filter_by(mes=mes_atual, ano=ano_atual).first()
        meta_valor_mes = float(meta_config.valor_loja) if meta_config else 1
        dias_uteis = meta_config.dias_uteis if meta_config and meta_config.dias_uteis > 0 else 1
        meta_diaria_alvo = meta_valor_mes / dias_uteis

        vendas_hoje = db.session.query(func.sum(Venda.valor_final))\
            .filter(func.date(Venda.criado_em) == hoje,
                    Venda.status != 'cancelada', Venda.status != 'orcamento').scalar() or 0
        
        atingimento_dia_perc = (float(vendas_hoje) / meta_diaria_alvo) * 100 if meta_diaria_alvo > 0 else 0

        # 3. A PAGAR
        a_pagar_mes = db.session.query(func.sum(Despesa.valor))\
            .filter(extract('month', Despesa.data_vencimento) == mes_atual,
                    extract('year', Despesa.data_vencimento) == ano_atual,
                    Despesa.status == 'pendente').scalar() or 0

        # 4. ALERTAS
        lista_vencidos = Despesa.query.filter(Despesa.status == 'pendente', Despesa.data_vencimento < hoje).order_by(Despesa.data_vencimento.asc()).all()
        limite_aviso = hoje + timedelta(days=5)
        lista_proximos = Despesa.query.filter(Despesa.status == 'pendente', Despesa.data_vencimento >= hoje, Despesa.data_vencimento <= limite_aviso).order_by(Despesa.data_vencimento.asc()).all()
        qtd_vencidos = len(lista_vencidos)
        qtd_proximos = len(lista_proximos)

        # 5. TICKET MÉDIO
        qtd_vendas_mes = db.session.query(func.count(Venda.id))\
            .filter(extract('month', Venda.criado_em) == mes_atual, 
                    extract('year', Venda.criado_em) == ano_atual,
                    Venda.status != 'cancelada', Venda.status != 'orcamento').scalar() or 0
        
        faturamento_mes = db.session.query(func.sum(Venda.valor_final))\
            .filter(extract('month', Venda.criado_em) == mes_atual, 
                    extract('year', Venda.criado_em) == ano_atual,
                    Venda.status != 'cancelada', Venda.status != 'orcamento').scalar() or 0
        
        ticket_medio = (float(faturamento_mes) / qtd_vendas_mes) if qtd_vendas_mes > 0 else 0
        perc_meta_mes = (float(faturamento_mes) / meta_valor_mes) * 100

        # 6. GRÁFICOS
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

        cats_db = db.session.query(Despesa.categoria, func.sum(Despesa.valor))\
            .filter(extract('month', Despesa.data_competencia) == mes_atual,
                    extract('year', Despesa.data_competencia) == ano_atual)\
            .group_by(Despesa.categoria).all()
        doughnut_labels = [c[0].title() for c in cats_db]
        doughnut_data = [float(c[1]) for c in cats_db]

    # === FIM DO BLOCO FINANCEIRO ===

    # =================================================================
    # --- INDICADORES OPERACIONAIS (SEMPRE VISÍVEIS) ---
    # =================================================================
    
    op_fila = db.session.query(ItemVenda).join(Venda).filter(ItemVenda.status == 'pendente', Venda.status != 'cancelada', Venda.status != 'orcamento').all()
    op_execucao = db.session.query(ItemVenda).join(Venda).filter(ItemVenda.status == 'producao', Venda.status != 'cancelada').all()
    op_prontos = db.session.query(ItemVenda).join(Venda).filter(ItemVenda.status == 'pronto', Venda.status != 'cancelada').all()
    op_finalizados = db.session.query(ItemVenda).join(Venda).filter(ItemVenda.status == 'entregue', extract('month', Venda.criado_em) == mes_atual, extract('year', Venda.criado_em) == ano_atual).all()

    # =================================================================
    # --- TOP PRODUTOS (ÚLTIMOS 30 DIAS) ---
    # =================================================================
    
    data_limite_30_dias = hoje - timedelta(days=30)
    
    # Busca vendas criadas nos últimos 30 dias
    top_produtos = db.session.query(CorServico.nome, func.sum(ItemVenda.quantidade).label('total_qtd'))\
        .join(ItemVenda, ItemVenda.cor_id == CorServico.id)\
        .join(Venda, ItemVenda.venda_id == Venda.id)\
        .filter(Venda.criado_em >= data_limite_30_dias,  # CORREÇÃO: Filtro de data
                Venda.status != 'cancelada')\
        .group_by(CorServico.nome)\
        .order_by(desc('total_qtd'))\
        .limit(5).all()

    return render_template('dashboard/painel.html',
                           exibir_financeiro=exibir_financeiro, # Flag para o HTML
                           
                           kpi_recebido=fmt_moeda(recebido_mes),
                           kpi_receber=fmt_moeda(a_receber),
                           vendas_hoje=fmt_moeda(vendas_hoje),
                           meta_diaria_alvo=fmt_moeda(meta_diaria_alvo),
                           atingimento_dia_perc=round(atingimento_dia_perc, 2),
                           kpi_pagar=fmt_moeda(a_pagar_mes),
                           qtd_vencidos=qtd_vencidos,
                           qtd_proximos=qtd_proximos,
                           lista_vencidos=lista_vencidos,
                           lista_proximos=lista_proximos,
                           
                           op_fila=op_fila,
                           op_execucao=op_execucao,
                           op_prontos=op_prontos,
                           op_finalizados=op_finalizados,
                           qtd_fila=len(op_fila),
                           qtd_execucao=len(op_execucao),
                           qtd_prontos=len(op_prontos),
                           qtd_finalizados=len(op_finalizados),

                           ticket_medio=fmt_moeda(ticket_medio),
                           top_produtos=top_produtos,

                           chart_labels=chart_labels,
                           chart_vendas=chart_data_vendas,
                           chart_despesas=chart_data_despesas,
                           doughnut_labels=doughnut_labels,
                           doughnut_data=doughnut_data,
                           meta_valor=fmt_moeda(meta_valor_mes),
                           perc_meta=round(perc_meta_mes, 2),
                           fmt_moeda=fmt_moeda)