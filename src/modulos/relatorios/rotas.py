from flask import render_template, request, send_file
from flask_login import login_required
from sqlalchemy import func, extract
from datetime import date
import io
import openpyxl

from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import Venda, ItemVenda
from src.modulos.autenticacao.permissoes import cargo_exigido
from . import bp_relatorios

@bp_relatorios.route('/')
@login_required
@cargo_exigido('relatorios_acesso')
def painel():
    return render_template('relatorios/painel.html')

@bp_relatorios.route('/servicos')
@login_required
@cargo_exigido('relatorios_acesso')
def relatorio_servicos():
    tipo_periodo = request.args.get('tipo_periodo', 'mes')
    mes = request.args.get('mes', date.today().month, type=int)
    ano = request.args.get('ano', date.today().year, type=int)
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    status_pagamento = request.args.get('status_pagamento', 'todos')
    status_servico = request.args.get('status_servico', 'todos')

    query = ItemVenda.query.join(Venda).filter(Venda.status != 'orcamento')

    if tipo_periodo == 'mes' and mes and ano:
        query = query.filter(extract('month', Venda.criado_em) == mes, extract('year', Venda.criado_em) == ano)
    elif tipo_periodo == 'periodo' and data_inicio and data_fim:
        query = query.filter(func.date(Venda.criado_em) >= data_inicio, func.date(Venda.criado_em) <= data_fim)

    if status_pagamento != 'todos':
        query = query.filter(Venda.status_pagamento == status_pagamento)
        
    if status_servico != 'todos':
        query = query.filter(ItemVenda.status == status_servico)

    itens = query.order_by(Venda.criado_em.desc(), ItemVenda.id.asc()).all()

    # --- ESTRUTURA PARA TABELA DINÂMICA (JSON) ---
    dados_json = []
    for item in itens:
        dados_json.append({
            'venda_id': item.venda_id,
            'data_fmt': item.venda.criado_em.strftime('%d/%m/%Y'),
            'cliente': item.venda.cliente_nome,
            'vendedor': item.venda.vendedor.nome if item.venda.vendedor else 'N/D',
            'item_desc': item.descricao,
            'produto': item.produto.nome if item.produto else (item.cor.nome if item.cor else 'Diversos'),
            'qtd': float(item.quantidade),
            'valor_unit': float(item.valor_unitario),
            'valor_total_item': float(item.valor_total),
            
            # Dados da Venda (Agrupados)
            'valor_total_venda': float(item.venda.valor_final),
            'valor_pago_venda': float(item.venda.valor_pago),
            'a_receber_venda': float(item.venda.valor_restante),
            
            # --- NOVOS DADOS PARA O CÁLCULO DE ACRÉSCIMO/DESCONTO ---
            'valor_acrescimo_venda': float(item.venda.valor_acrescimo or 0),
            'valor_desconto_venda': float(item.venda.valor_desconto_aplicado or 0),
            'qtd_itens_venda': len(item.venda.itens),
            
            'status_prod_item': item.status,
            'status_prod_venda': item.venda.status,
            'status_pgto': item.venda.status_pagamento
        })

    # --- EXPORTAR PARA EXCEL ---
    if request.args.get('exportar') == 'excel':
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Relatório Eletromaster"
        
        ws.append([
            "ID Venda", "Data", "Cliente", "Vendedor", 
            "Item", "Acabamento", "Qtd", "V. Unitário", "V. Total Item", 
            "Acréscimo / Desconto", # <--- NOVA COLUNA AQUI
            "Total da Venda", "Total Pago", "A Receber (Restante)", 
            "Status Produção", "Status Pgto"
        ])
        
        for d in dados_json:
            # Excel exporta granular (por item), então aplicamos a divisão matemática
            saldo_extra_item = 0
            if d['qtd_itens_venda'] > 0:
                saldo_extra_item = (d['valor_acrescimo_venda'] - d['valor_desconto_venda']) / d['qtd_itens_venda']
                
            ws.append([
                d['venda_id'], d['data_fmt'], d['cliente'], d['vendedor'],
                d['item_desc'], d['produto'], d['qtd'], 
                d['valor_unit'], d['valor_total_item'],
                saldo_extra_item, # <--- APLICA O RATEIO NO EXCEL
                d['valor_total_venda'], d['valor_pago_venda'], d['a_receber_venda'],
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

    # --- CÁLCULOS PARA OS CARDS SUPERIORES ---
    vendas_unicas = {item.venda for item in itens}
    total_valor = sum(float(v.valor_final) for v in vendas_unicas)
    total_pago = sum(float(v.valor_pago) for v in vendas_unicas)
    total_restante = sum(float(v.valor_restante) for v in vendas_unicas)

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