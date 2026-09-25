from flask import render_template, request
from flask_login import login_required
from sqlalchemy import func
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import calendar

from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import Venda, Pagamento
from src.modulos.autenticacao.permissoes import cargo_exigido
from src.modulos.autenticacao.modelos import Usuario
from src.modulos.rh.modelos import Colaborador
from src.modulos.relatorios import bp_relatorios

MESES_ABREV = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']

def semana_do_mes(dt):
    """
    Retorna (numero_semana, data_inicio, data_fim) usando blocos fixos de 7 dias:
      Semana 1: dias 1-7
      Semana 2: dias 8-14
      Semana 3: dias 15-21
      Semana 4: dias 22-28
      Semana 5: dias 29-fim
    """
    num = (dt.day - 1) // 7 + 1  # 1 a 5
    start_day = (num - 1) * 7 + 1
    last_day = calendar.monthrange(dt.year, dt.month)[1]
    end_day = min(start_day + 6, last_day)
    return num, dt.replace(day=start_day), dt.replace(day=end_day)

def mesmo_periodo_semana_anterior(dt):
    """Retorna (ini, fim) para a mesma semana-do-mês no mês anterior."""
    num, _, _ = semana_do_mes(dt)
    prev = dt - relativedelta(months=1)
    last_day_prev = calendar.monthrange(prev.year, prev.month)[1]
    start_day = (num - 1) * 7 + 1
    if start_day > last_day_prev:          # semana 5 pode não existir
        start_day = last_day_prev - 6
    end_day = min(start_day + 6, last_day_prev)
    return prev.replace(day=start_day), prev.replace(day=end_day)

@bp_relatorios.route('/servicos')
@login_required
@cargo_exigido('relatorios_servicos')
def relatorio_servicos():
    hoje = date.today()

    # ── Filtros ─────────────────────────────────────────────────────────────
    data_inicio_str = request.args.get('data_inicio')
    data_fim_str    = request.args.get('data_fim')
    status_pagamento = request.args.get('status_pagamento', 'todos')
    funil      = request.args.get('funil', 'todos')
    vendedor_id = request.args.get('vendedor', 'todos')

    if not data_inicio_str or not data_fim_str:
        data_inicio = hoje.replace(day=1)
        data_fim    = hoje   # padrão: do 1º até hoje
    else:
        data_inicio = datetime.strptime(data_inicio_str, '%Y-%m-%d').date()
        data_fim    = datetime.strptime(data_fim_str,    '%Y-%m-%d').date()

    def aplica_filtros_venda(q):
        if status_pagamento != 'todos':
            q = q.filter(Venda.status_pagamento == status_pagamento)
        if funil != 'todos':
            q = q.filter(Venda.funil == funil)
        if vendedor_id != 'todos':
            q = q.filter(Venda.vendedor_id == int(vendedor_id))
        return q

    # ── KPI Total a Receber (ignora data de pagamento) ───────────────────────
    q_receber = aplica_filtros_venda(
        db.session.query(Venda).filter(
            Venda.status != 'cancelado', Venda.status != 'orcamento'
        )
    )
    
    aging_receber = {
        '0-10 dias': 0.0,
        '11-20 dias': 0.0,
        '21-30 dias': 0.0,
        '31+ dias': 0.0
    }
    detalhes_aging = {
        '0-10 dias': [],
        '11-20 dias': [],
        '21-30 dias': [],
        '31+ dias': []
    }
    
    total_a_receber = 0.0
    for v in q_receber.all():
        val_rest = float(v.valor_restante)
        if val_rest > 0:
            total_a_receber += val_rest
            if v.criado_em:
                dias = (hoje - v.criado_em.date()).days
            else:
                dias = 0
                
            if dias <= 10:
                faixa = '0-10 dias'
            elif dias <= 20:
                faixa = '11-20 dias'
            elif dias <= 30:
                faixa = '21-30 dias'
            else:
                faixa = '31+ dias'
                
            aging_receber[faixa] += val_rest
            detalhes_aging[faixa].append({
                'servico_id': v.id,
                'cliente': v.cliente_nome or 'N/D',
                'valor': val_rest,
                'data': v.criado_em.strftime('%d/%m/%Y') if v.criado_em else '',
                'dias': dias
            })

    # ── KPI Total Recebido + dados dos gráficos ──────────────────────────────
    q_pgtos = aplica_filtros_venda(
        db.session.query(Pagamento, Venda)
        .join(Venda, Pagamento.venda_id == Venda.id)
        .filter(Venda.status != 'cancelado', Venda.status != 'orcamento')
    )
    q_pgtos_periodo = q_pgtos.filter(
        func.date(Pagamento.data_pagamento) >= data_inicio,
        func.date(Pagamento.data_pagamento) <= data_fim
    )

    total_recebido   = 0.0
    por_vendedor     = {}
    por_funil        = {}
    detalhes_vendedor = {}

    for p, v in q_pgtos_periodo.all():
        val = float(p.valor)
        total_recebido += val
        vend = (v.vendedor.colaborador.nome_completo
                if v.vendedor and v.vendedor.colaborador
                else (v.vendedor.usuario if v.vendedor else 'N/D'))
        fn = v.funil or 'Não Informado'
        por_vendedor[vend] = por_vendedor.get(vend, 0) + val
        por_funil[fn]      = por_funil.get(fn, 0) + val

        if vend not in detalhes_vendedor:
            detalhes_vendedor[vend] = []
        detalhes_vendedor[vend].append({
            'cliente': v.cliente_nome or 'N/D',
            'valor': val,
            'data': p.data_pagamento.strftime('%d/%m/%Y') if p.data_pagamento else ''
        })

    # ── Pareto: acumulado (gráfico) + participação (tabela) ─────────────────
    pareto_data = sorted(
        [{'vendedor': k, 'valor': v} for k, v in por_vendedor.items()],
        key=lambda x: x['valor'], reverse=True
    )
    acum = 0.0
    for item in pareto_data:
        item['perc_participacao'] = (item['valor'] / total_recebido * 100) if total_recebido > 0 else 0
        acum += item['valor']
        item['perc_acumulado']   = (acum / total_recebido * 100) if total_recebido > 0 else 0

    # ── Rosca funil ──────────────────────────────────────────────────────────
    rosca_labels = list(por_funil.keys())
    rosca_values = list(por_funil.values())

    # ── Comparativo (Linha projetada Diária e Mensal) ───────────────────────────
    data_ref = data_fim

    def get_pagamentos_no_intervalo(ini, fim):
        q = aplica_filtros_venda(
            db.session.query(Pagamento.data_pagamento, Pagamento.valor)
            .join(Venda)
            .filter(
                Venda.status != 'cancelado', Venda.status != 'orcamento',
                func.date(Pagamento.data_pagamento) >= ini,
                func.date(Pagamento.data_pagamento) <= fim
            )
        )
        return q.all()

    # == Visão Diária ==
    mes_atual_ini = data_ref.replace(day=1)
    # Lidar com meses que não tem 31 dias usando monthrange para o limite real do mês,
    # embora o array fixo tenha 31 posições (dias 1..31).
    _, ult_dia = calendar.monthrange(mes_atual_ini.year, mes_atual_ini.month)
    mes_atual_fim = mes_atual_ini.replace(day=ult_dia)
    pgtos_mes_atual = get_pagamentos_no_intervalo(mes_atual_ini, mes_atual_fim)

    mes_ant_ini = mes_atual_ini - relativedelta(months=1)
    _, ult_dia_ant = calendar.monthrange(mes_ant_ini.year, mes_ant_ini.month)
    mes_ant_fim = mes_ant_ini.replace(day=ult_dia_ant)
    pgtos_mes_ant = get_pagamentos_no_intervalo(mes_ant_ini, mes_ant_fim)

    dias_do_mes = [str(d) for d in range(1, 32)]
    val_diario_atual = [0.0] * 31
    val_diario_ant = [0.0] * 31

    for p in pgtos_mes_atual:
        if p.data_pagamento:
            val_diario_atual[p.data_pagamento.day - 1] += float(p.valor)

    for p in pgtos_mes_ant:
        if p.data_pagamento:
            val_diario_ant[p.data_pagamento.day - 1] += float(p.valor)

    lbl_mes_atual = f"{MESES_ABREV[mes_atual_ini.month-1]} {str(mes_atual_ini.year)[2:]}"
    lbl_mes_ant = f"{MESES_ABREV[mes_ant_ini.month-1]} {str(mes_ant_ini.year)[2:]}"

    # == Visão Mensal ==
    ano_atual_ini = data_ref.replace(month=1, day=1)
    ano_atual_fim = data_ref.replace(month=12, day=31)
    pgtos_ano_atual = get_pagamentos_no_intervalo(ano_atual_ini, ano_atual_fim)

    ano_ant_ini = ano_atual_ini.replace(year=ano_atual_ini.year - 1)
    ano_ant_fim = ano_atual_fim.replace(year=ano_atual_fim.year - 1)
    pgtos_ano_ant = get_pagamentos_no_intervalo(ano_ant_ini, ano_ant_fim)

    val_mensal_atual = [0.0] * 12
    val_mensal_ant = [0.0] * 12

    for p in pgtos_ano_atual:
        if p.data_pagamento:
            val_mensal_atual[p.data_pagamento.month - 1] += float(p.valor)
            
    for p in pgtos_ano_ant:
        if p.data_pagamento:
            val_mensal_ant[p.data_pagamento.month - 1] += float(p.valor)

    lbl_ano_atual = str(ano_atual_ini.year)
    lbl_ano_ant = str(ano_ant_ini.year)

    comp_vendas = {
        'diario': {
            'labels': dias_do_mes,
            'atual': val_diario_atual,
            'anterior': val_diario_ant,
            'lbl_atual': lbl_mes_atual,
            'lbl_anterior': lbl_mes_ant
        },
        'mensal': {
            'labels': MESES_ABREV,
            'atual': val_mensal_atual,
            'anterior': val_mensal_ant,
            'lbl_atual': lbl_ano_atual,
            'lbl_anterior': lbl_ano_ant
        }
    }

    # ── Vendedores para o filtro ─────────────────────────────────────────────
    vendedores_q = (
        db.session.query(Usuario.id, Colaborador.nome_completo, Usuario.usuario)
        .outerjoin(Colaborador, Usuario.colaborador_id == Colaborador.id)
        .join(Venda, Venda.vendedor_id == Usuario.id)
        .distinct().all()
    )
    vendedores   = [{'id': v[0], 'nome': v[1] if v[1] else v[2]} for v in vendedores_q]
    opcoes_funil = ["Indicação","Captação","Lead","Visita","Resgate","Google","Cliente da Base"]

    def fmt_moeda(valor):
        if not valor: return "0,00"
        return f"{float(valor):,.2f}".replace(",","X").replace(".","," ).replace("X",".")

    return render_template('relatorios/servicos.html',
        filtros=request.args,
        data_inicio=data_inicio.strftime('%Y-%m-%d'),
        data_fim=data_fim.strftime('%Y-%m-%d'),
        total_vendido=fmt_moeda(total_recebido),
        total_a_receber=fmt_moeda(total_a_receber),
        pareto_data=pareto_data,
        rosca_labels=rosca_labels,
        rosca_values=rosca_values,
        comp_vendas=comp_vendas,
        vendedores=vendedores,
        opcoes_funil=opcoes_funil,
        detalhes_vendedor=detalhes_vendedor,
        aging_receber=aging_receber,
        detalhes_aging=detalhes_aging,
        fmt_moeda=fmt_moeda,
    )