from flask import render_template, request, send_file
from flask_login import login_required
from sqlalchemy import func, extract
from datetime import date, datetime
import io
import openpyxl

from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import Venda, ItemVenda, Pagamento
from src.modulos.autenticacao.permissoes import cargo_exigido
from src.modulos.relatorios import bp_relatorios

@bp_relatorios.route('/servicos')
@login_required
@cargo_exigido('relatorios_servicos')
def relatorio_servicos():
    tipo_periodo = request.args.get('tipo_periodo', 'mes')
    mes = request.args.get('mes', date.today().month, type=int)
    ano = request.args.get('ano', date.today().year, type=int)
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    status_pagamento = request.args.get('status_pagamento', 'todos')
    status_servico = request.args.get('status_servico', 'todos')
    tipo_data_filtro = request.args.get('tipo_data_filtro', 'criacao')

    query = ItemVenda.query.join(Venda).filter(Venda.status != 'orcamento')

    # ===============================================
    # LÓGICA DE FILTRO DE DATA
    # ===============================================
    if tipo_data_filtro == 'recebimento':
        if tipo_periodo == 'mes' and mes and ano:
            subq = db.session.query(Pagamento.venda_id).filter(
                extract('month', Pagamento.data_pagamento) == mes, 
                extract('year', Pagamento.data_pagamento) == ano
            )
        elif tipo_periodo == 'periodo' and data_inicio and data_fim:
            subq = db.session.query(Pagamento.venda_id).filter(
                func.date(Pagamento.data_pagamento) >= data_inicio, 
                func.date(Pagamento.data_pagamento) <= data_fim
            )
        else:
            subq = None
            
        if subq is not None:
            query = query.filter(Venda.id.in_(subq))
    else:
        if tipo_periodo == 'mes' and mes and ano:
            query = query.filter(extract('month', Venda.criado_em) == mes, extract('year', Venda.criado_em) == ano)
        elif tipo_periodo == 'periodo' and data_inicio and data_fim:
            query = query.filter(func.date(Venda.criado_em) >= data_inicio, func.date(Venda.criado_em) <= data_fim)

    if status_pagamento != 'todos':
        query = query.filter(Venda.status_pagamento == status_pagamento)
        
    if status_servico != 'todos':
        if status_servico == 'cancelado':
            query = query.filter(Venda.status == 'cancelado')
        else:
            query = query.filter(ItemVenda.status == status_servico, Venda.status != 'cancelado')

    itens = query.order_by(Venda.criado_em.desc(), ItemVenda.id.asc()).all()

    # Prepara as datas para o filtro exato
    d_ini, d_fim = None, None
    if tipo_periodo == 'periodo' and data_inicio and data_fim:
        try:
            d_ini = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            d_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        except ValueError: pass

    dados_json = []
    for item in itens:
        # ===============================================
        # EXTRAÇÃO INTELIGENTE DE PAGAMENTOS
        # ===============================================
        pagamentos_detalhados = []
        valor_pago_no_periodo = 0.0

        for p in sorted(item.venda.pagamentos, key=lambda x: x.data_pagamento):
            incluir = True
            
            # Se o filtro é por recebimento, ocultar valores e datas que estão fora do mês/período filtrado
            if tipo_data_filtro == 'recebimento':
                p_date = p.data_pagamento.date() if hasattr(p.data_pagamento, 'date') else p.data_pagamento
                if tipo_periodo == 'mes' and mes and ano:
                    if p_date.month != mes or p_date.year != ano: incluir = False
                elif tipo_periodo == 'periodo' and d_ini and d_fim:
                    if not (d_ini <= p_date <= d_fim): incluir = False
            
            if incluir:
                pagamentos_detalhados.append({
                    'data': p.data_pagamento.strftime('%d/%m/%Y'),
                    'valor': float(p.valor)
                })
                valor_pago_no_periodo += float(p.valor)

        texto_excel_pgtos = "\n".join([f"{p['data']}: R$ {p['valor']:.2f}".replace('.', ',') for p in pagamentos_detalhados])
        if not texto_excel_pgtos: texto_excel_pgtos = "-"

        dados_json.append({
            'venda_id': item.venda_id,
            'data_fmt': item.venda.criado_em.strftime('%d/%m/%Y'),
            'pagamentos_detalhados': pagamentos_detalhados, # <-- Lista enviada ao JS
            'texto_excel_pgtos': texto_excel_pgtos,
            'cliente': item.venda.cliente_nome,
            'vendedor': item.venda.vendedor.nome if item.venda.vendedor else 'N/D',
            'item_desc': item.descricao,
            'produto': item.produto.nome if item.produto else (item.cor.nome if item.cor else 'Diversos'),
            'qtd': float(item.quantidade),
            'valor_unit': float(item.valor_unitario),
            'valor_total_item': float(item.valor_total),
            'valor_total_venda': float(item.venda.valor_final),
            'valor_pago_venda': valor_pago_no_periodo, # <-- AQUI ESTÁ O SEGREDO (Soma apenas o valor do filtro)
            'a_receber_venda': float(item.venda.valor_restante),
            'valor_acrescimo_venda': float(item.venda.valor_acrescimo or 0),
            'valor_desconto_venda': float(item.venda.valor_desconto_aplicado or 0),
            'qtd_itens_venda': len(item.venda.itens),
            'status_prod_item': item.status,
            'status_prod_venda': item.venda.status,
            'status_pgto': item.venda.status_pagamento
        })

    # ===============================================
    # EXPORTAÇÃO PARA O EXCEL ATUALIZADA
    # ===============================================
    if request.args.get('exportar') == 'excel':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Relatório Eletromaster"
        
        ws.append([
            "ID Venda", "Data Criação", "Data Recebimento e Valor", "Cliente", "Vendedor", 
            "Item", "Acabamento", "Qtd", "V. Unitário", "V. Total Item", 
            "Acréscimo / Desconto", "Total da Venda", "Total Recebido (Período)", "A Receber (Restante da Venda)", 
            "Status Produção", "Status Pgto"
        ])
        
        for d in dados_json:
            saldo_extra_item = 0
            if d['qtd_itens_venda'] > 0:
                saldo_extra_item = (d['valor_acrescimo_venda'] - d['valor_desconto_venda']) / d['qtd_itens_venda']
                
            ws.append([
                d['venda_id'], d['data_fmt'], d['texto_excel_pgtos'], d['cliente'], d['vendedor'],
                d['item_desc'], d['produto'], d['qtd'], d['valor_unit'], d['valor_total_item'],
                saldo_extra_item, d['valor_total_venda'], d['valor_pago_venda'], d['a_receber_venda'],
                d['status_prod_item'].upper(), d['status_pgto'].upper()
            ])
            
        out = io.BytesIO()
        wb.save(out)
        out.seek(0)
        
        return send_file(
            out,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'relatorio_eletromaster_{date.today().strftime("%d%m%Y")}.xlsx'
        )

    # ===============================================
    # CÁLCULO DOS CARDS (KPIs) SEGUROS
    # ===============================================
    vendas_unicas = {item.venda for item in itens}
    total_valor = sum(float(v.valor_final) for v in vendas_unicas if v.status != 'cancelado')
    total_restante = sum(float(v.valor_restante) for v in vendas_unicas if v.status != 'cancelado')
    
    total_pago = 0
    for v in vendas_unicas:
        if v.status == 'cancelado': continue
        # Soma para o CARD apenas o que entrou no período filtrado
        for p in v.pagamentos:
            incluir = True
            if tipo_data_filtro == 'recebimento':
                p_date = p.data_pagamento.date() if hasattr(p.data_pagamento, 'date') else p.data_pagamento
                if tipo_periodo == 'mes' and mes and ano:
                    if p_date.month != mes or p_date.year != ano: incluir = False
                elif tipo_periodo == 'periodo' and d_ini and d_fim:
                    if not (d_ini <= p_date <= d_fim): incluir = False
            if incluir:
                total_pago += float(p.valor)

    return render_template('relatorios/servicos.html', 
                           filtros=request.args,
                           total_valor=total_valor,
                           total_pago=total_pago,
                           total_restante=total_restante,
                           qtd_servicos=len(vendas_unicas),
                           qtd_itens=len(itens),
                           mes_atual=mes,
                           ano_atual=ano,
                           dados_json=dados_json)