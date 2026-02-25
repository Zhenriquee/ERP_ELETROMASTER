from flask import render_template, request
from flask_login import login_required, current_user
from sqlalchemy import extract, desc, and_
from datetime import date
from src.modulos.autenticacao.permissoes import cargo_exigido

from src.extensoes import banco_de_dados as db
from src.modulos.financeiro.modelos import Despesa, Fornecedor
from . import bp_financeiro
from sqlalchemy import extract, desc, and_, or_

@bp_financeiro.route('/', methods=['GET'])
@login_required
@cargo_exigido('financeiro_acesso')
def painel():
    hoje = date.today()
    
    # ============================================================
    # 1. PREPARAÇÃO DOS FILTROS (PERIODOS E LISTAS)
    # ============================================================
    competencias_db = db.session.query(
            extract('year', Despesa.data_vencimento).label('ano'),
            extract('month', Despesa.data_vencimento).label('mes')
        ).group_by('ano', 'mes').all()
    
    lista_competencias = []
    for ano, mes in competencias_db:
        lista_competencias.append((int(ano), int(mes)))

    if (hoje.year, hoje.month) not in lista_competencias:
        lista_competencias.append((hoje.year, hoje.month))
    
    lista_competencias.sort(key=lambda x: (x[0], x[1]), reverse=True)

    periodos = []
    mapa_meses = {1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'}

    for ano, mes in lista_competencias:
        periodos.append({'valor': f"{mes}-{ano}", 'label': f"{mapa_meses[mes]} {ano}", 'mes': mes, 'ano': ano})

    fornecedores = Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome_fantasia).all()

    # ============================================================
    # 2. CAPTURA DOS PARÂMETROS DA URL
    # ============================================================
    mes_padrao = hoje.month
    ano_padrao = hoje.year

    mes = request.args.get('mes', mes_padrao, type=int)
    ano = request.args.get('ano', ano_padrao, type=int)
    
    # --- NOVA LÓGICA: FORÇA O MÊS/ANO DA CONTA DESTACADA ---
    destaque_id = request.args.get('destaque_id', type=int)
    if destaque_id:
        despesa_destaque = Despesa.query.get(destaque_id)
        if despesa_destaque:
            mes = despesa_destaque.data_vencimento.month
            ano = despesa_destaque.data_vencimento.year

    # Filtros Avançados
    f_busca = request.args.get('q', '').strip() 
    f_categoria = request.args.get('categoria', '')
    f_vencimento = request.args.get('vencimento', '')
    f_forma_pagamento = request.args.get('forma_pagamento', '')
    f_tipo_custo = request.args.get('tipo_custo', '')
    f_fornecedor = request.args.get('fornecedor', type=int)
    f_status = request.args.get('status', '')

    # ============================================================
    # 3. QUERY PRINCIPAL (LISTA)
    # ============================================================
    query = Despesa.query.filter(
        extract('month', Despesa.data_vencimento) == mes,
        extract('year', Despesa.data_vencimento) == ano
    )
    
    if f_busca:
        if f_busca.isdigit():
            query = query.filter(or_(Despesa.id == int(f_busca), Despesa.descricao.ilike(f'%{f_busca}%')))
        else:
            query = query.filter(Despesa.descricao.ilike(f'%{f_busca}%'))
            
    if f_status:
        query = query.filter(Despesa.status == f_status)
    if f_categoria:
        query = query.filter(Despesa.categoria == f_categoria)
    if f_forma_pagamento:
        query = query.filter(Despesa.forma_pagamento == f_forma_pagamento)
    if f_tipo_custo:
        query = query.filter(Despesa.tipo_custo == f_tipo_custo)
    if f_fornecedor:
        query = query.filter(Despesa.fornecedor_id == f_fornecedor)
    if f_vencimento:
        query = query.filter(Despesa.data_vencimento == f_vencimento)

    despesas = query.order_by(Despesa.status.asc(), Despesa.data_vencimento.asc()).all()
    
    # ============================================================
    # 4. CÁLCULO DE TOTAIS (KPIS)
    # ============================================================
    total_pendente = sum(d.valor for d in despesas if d.status == 'pendente')
    total_pago = sum(d.valor for d in despesas if d.status == 'pago')
    
    total_vencido_geral = db.session.query(db.func.sum(Despesa.valor))\
        .filter(Despesa.status == 'pendente', Despesa.data_vencimento < hoje)\
        .scalar() or 0
    
    pode_ver_totais = current_user.tem_permissao('financeiro_cards') or current_user.cargo.lower() == 'dono'

    return render_template('financeiro/painel.html', 
                           despesas=despesas, 
                           periodos=periodos, 
                           periodo_selecionado=f"{mes}-{ano}",
                           fornecedores=fornecedores,
                           total_pendente=total_pendente,
                           total_pago=total_pago,
                           total_vencido_geral=total_vencido_geral,
                           pode_ver_totais=pode_ver_totais,
                           destaque_id=destaque_id, # <--- ENVIADO PARA O HTML
                           filtros={
                               'q': f_busca,
                               'categoria': f_categoria,
                               'vencimento': f_vencimento,
                               'forma_pagamento': f_forma_pagamento,
                               'tipo_custo': f_tipo_custo,
                               'fornecedor': f_fornecedor,
                               'status': f_status
                           })