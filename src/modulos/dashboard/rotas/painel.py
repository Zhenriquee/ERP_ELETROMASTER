from flask import render_template
from flask_login import login_required
from sqlalchemy import func, extract
from datetime import date
from dateutil.relativedelta import relativedelta

from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import Venda, Pagamento
from src.modulos.financeiro.modelos import Despesa
from src.modulos.metas.modelos import MetaMensal
from src.modulos.autenticacao.modelos import Usuario
from src.modulos.dashboard import bp_dashboard # Importa o BP do módulo pai

def fmt_moeda(valor):
    if not valor: return "0,00"
    return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@bp_dashboard.route('/')
@login_required
def painel():
    hoje = date.today()
    mes_atual = hoje.month
    ano_atual = hoje.year

    # 1. KPIs FINANCEIROS E VENDAS
    faturamento_mes = db.session.query(func.sum(Venda.valor_final))\
        .filter(extract('month', Venda.criado_em) == mes_atual, 
                extract('year', Venda.criado_em) == ano_atual,
                Venda.status != 'cancelada', Venda.status != 'orcamento').scalar() or 0

    total_vendido_geral = db.session.query(func.sum(Venda.valor_final)).filter(Venda.status != 'cancelada', Venda.status != 'orcamento').scalar() or 0
    total_pago_geral = db.session.query(func.sum(Pagamento.valor)).scalar() or 0
    a_receber = total_vendido_geral - total_pago_geral

    a_pagar_mes = db.session.query(func.sum(Despesa.valor))\
        .filter(extract('month', Despesa.data_vencimento) == mes_atual,
                extract('year', Despesa.data_vencimento) == ano_atual,
                Despesa.status == 'pendente').scalar() or 0

    equipe_ativa = Usuario.query.filter_by(ativo=True).count()

    # 2. DADOS PARA O GRÁFICO DE LINHA (6 Meses)
    chart_labels = []
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

    # 3. DADOS PARA GRÁFICO DE ROSCA
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

    # 4. META DO MÊS
    meta = MetaMensal.query.filter_by(mes=mes_atual, ano=ano_atual).first()
    meta_valor = float(meta.valor_loja) if meta else 1 
    perc_meta = (float(faturamento_mes) / meta_valor) * 100
    
    # --- CORREÇÃO AQUI ---
    # Calculamos o valor limite (100)
    valor_limite = 100 if perc_meta > 100 else perc_meta
    
    # Criamos a string CSS pronta. Ex: "85.5%"
    # Isso evita que o HTML tenha que concatenar o "%", o que confunde o editor.
    largura_barra_css = f"{valor_limite:.1f}%"

    return render_template('dashboard/painel.html',
                           kpi_faturamento=fmt_moeda(faturamento_mes),
                           kpi_receber=fmt_moeda(a_receber),
                           kpi_pagar=fmt_moeda(a_pagar_mes),
                           kpi_equipe=equipe_ativa,
                           chart_labels=chart_labels,
                           chart_vendas=chart_data_vendas,
                           chart_despesas=chart_data_despesas,
                           doughnut_labels=doughnut_labels,
                           doughnut_data=doughnut_data,
                           meta_valor=fmt_moeda(meta_valor) if meta else "Não definida",
                           perc_meta=round(perc_meta, 1),
                           largura_barra=largura_barra_css) # Passamos a nova variável