from flask import render_template, request, send_file
from flask_login import login_required
from sqlalchemy import func, extract
from datetime import date
import io
import openpyxl

from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import Venda, ItemVenda
from src.modulos.estoque.modelos import MovimentacaoEstoque, ProdutoEstoque
from src.modulos.autenticacao.permissoes import cargo_exigido
from src.modulos.relatorios import bp_relatorios

@bp_relatorios.route('/consumo-materiais')
@login_required
@cargo_exigido('relatorios_acesso')
def relatorio_consumo():
    tipo_periodo = request.args.get('tipo_periodo', 'mes')
    mes = request.args.get('mes', date.today().month, type=int)
    ano = request.args.get('ano', date.today().year, type=int)
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    produto_id = request.args.get('produto_id', 'todos')
    
    # Parâmetros de Paginação
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)

    # Base da Query
    base_query = db.session.query(
        MovimentacaoEstoque, ProdutoEstoque, ItemVenda, Venda
    ).join(
        ProdutoEstoque, MovimentacaoEstoque.produto_id == ProdutoEstoque.id
    ).outerjoin(
        ItemVenda, db.and_(
            MovimentacaoEstoque.referencia_id == ItemVenda.id,
            MovimentacaoEstoque.origem == 'producao'
        )
    ).outerjoin(
        Venda, ItemVenda.venda_id == Venda.id
    ).filter(
        MovimentacaoEstoque.tipo == 'saida'
    )

    # Filtros
    if tipo_periodo == 'mes' and mes and ano:
        base_query = base_query.filter(extract('month', MovimentacaoEstoque.data_movimentacao) == mes, 
                                     extract('year', MovimentacaoEstoque.data_movimentacao) == ano)
    elif tipo_periodo == 'periodo' and data_inicio and data_fim:
        base_query = base_query.filter(func.date(MovimentacaoEstoque.data_movimentacao) >= data_inicio, 
                                     func.date(MovimentacaoEstoque.data_movimentacao) <= data_fim)

    if produto_id != 'todos':
        base_query = base_query.filter(ProdutoEstoque.id == int(produto_id))

    # CÁLCULO GERAL RÁPIDO (Acontece antes de paginar para mostrar os KPIs no topo da tela)
    qtd_registros = base_query.count()
    total_consumido = base_query.with_entities(func.sum(MovimentacaoEstoque.quantidade)).scalar() or 0

    # EXPORTAÇÃO EXCEL: Aqui ignoramos a paginação e exportamos tudo.
    if request.args.get('exportar') == 'excel':
        resultados = base_query.order_by(MovimentacaoEstoque.data_movimentacao.desc()).all()
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Consumo de Materiais"
        ws.append(["Data/Hora", "Material", "Unidade", "Qtd Consumida", "Origem", "ID Serviço", "Item Solicitado", "Cliente", "Responsável"])
        
        for mov, prod, item, venda in resultados:
            ws.append([
                mov.data_movimentacao.strftime('%d/%m/%Y %H:%M'), 
                prod.nome, prod.unidade, float(mov.quantidade), mov.origem.upper(),
                venda.id if venda else '-', item.descricao if item else mov.observacao, 
                venda.cliente_nome if venda else 'Uso Interno / Manual', 
                mov.usuario.nome if mov.usuario else 'Sistema'
            ])
            
        out = io.BytesIO()
        wb.save(out)
        out.seek(0)
        return send_file(out, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', as_attachment=True, download_name=f'relatorio_consumo_{date.today().strftime("%d%m%Y")}.xlsx')

    # EXECUÇÃO COM PAGINAÇÃO NO BANCO (Só carrega as x linhas da página)
    paginacao = base_query.order_by(MovimentacaoEstoque.data_movimentacao.desc()).paginate(page=page, per_page=per_page, error_out=False)

    dados_json = []
    for mov, prod, item, venda in paginacao.items:
        dados_json.append({
            'data_fmt': mov.data_movimentacao.strftime('%d/%m/%Y %H:%M'),
            'produto': prod.nome,
            'unidade': prod.unidade,
            'qtd': float(mov.quantidade),
            'origem': mov.origem,
            'servico_id': venda.id if venda else '-',
            'item_desc': item.descricao if item else mov.observacao,
            'cliente': venda.cliente_nome if venda else 'Uso Interno / Ajuste Manual',
            'operador': mov.usuario.nome if mov.usuario else 'Sistema'
        })

    produtos_lista = ProdutoEstoque.query.order_by(ProdutoEstoque.nome).all()

    return render_template('relatorios/consumo_materiais.html',
                           filtros=request.args,
                           dados_json=dados_json,
                           produtos=produtos_lista,
                           total_consumido=total_consumido,
                           qtd_registros=qtd_registros,
                           mes_atual=mes,
                           ano_atual=ano,
                           paginacao=paginacao,
                           per_page=per_page)