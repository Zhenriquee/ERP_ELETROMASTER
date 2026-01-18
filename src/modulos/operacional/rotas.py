from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import ItemVenda, Venda, hora_brasilia
from src.modulos.autenticacao.permissoes import cargo_exigido

bp_operacional = Blueprint('operacional', __name__, url_prefix='/operacional')

@bp_operacional.route('/painel')
@login_required
@cargo_exigido('producao_operar')
def painel():
    # 1. Busca ITENS de Vendas Múltiplas
    itens_multi = ItemVenda.query.join(Venda).filter(
        ItemVenda.status.in_(['pendente', 'producao', 'pronto']),
        Venda.status != 'cancelado',
        Venda.status != 'orcamento'
    ).all()

    # 2. Busca VENDAS SIMPLES (Metragem/Unitária) que não têm itens na tabela ItemVenda
    vendas_simples = Venda.query.filter(
        Venda.modo == 'simples',
        Venda.status.in_(['pendente', 'producao', 'pronto']),
        Venda.status != 'orcamento'
    ).all()

    # 3. Unifica tudo em uma lista de dicionários ("Tarefas")
    tarefas = []

    # Processa Itens Múltiplos
    for i in itens_multi:
        tarefas.append({
            'tipo': 'item', # Identificador para saber qual rota chamar
            'id': i.id,
            'venda_id': i.venda_id,
            'descricao': i.descricao,
            'quantidade': i.quantidade,
            'cor': i.cor.nome,
            'status': i.status,
            'cliente': i.venda.cliente_nome,
            'obs': i.venda.observacoes_internas,
            'criado_em': i.venda.criado_em,
            'is_producao': (i.status == 'producao') # Auxiliar para ordenação
        })

    # Processa Vendas Simples
    for v in vendas_simples:
        tarefas.append({
            'tipo': 'venda', # Identificador para saber qual rota chamar
            'id': v.id,
            'venda_id': v.id,
            'descricao': v.descricao_servico,
            'quantidade': v.quantidade_pecas,
            'cor': v.cor.nome if v.cor else 'Padrão',
            'status': v.status,
            'cliente': v.cliente_nome,
            'obs': v.observacoes_internas,
            'criado_em': v.criado_em,
            'is_producao': (v.status == 'producao')
        })

    # Ordenação Inteligente: 
    # 1º O que está em Produção
    # 2º Os mais antigos (FIFO)
    tarefas.sort(key=lambda x: (not x['is_producao'], x['criado_em']))

    # Contadores Unificados
    qtd_fila = sum(1 for t in tarefas if t['status'] == 'pendente')
    qtd_producao = sum(1 for t in tarefas if t['status'] == 'producao')
    qtd_pronto = sum(1 for t in tarefas if t['status'] == 'pronto')

    return render_template('operacional/painel.html', 
                           tarefas=tarefas,
                           qtd_fila=qtd_fila, 
                           qtd_producao=qtd_producao, 
                           qtd_pronto=qtd_pronto)

# --- ROTAS DE AÇÃO PARA ITENS (Venda Múltipla) ---

@bp_operacional.route('/item/<int:id>/avancar')
@login_required
@cargo_exigido('producao_operar')
def avancar_item(id):
    item = ItemVenda.query.get_or_404(id)
    venda_pai = Venda.query.get(item.venda_id)
    agora = hora_brasilia()

    if item.status == 'pendente':
        item.status = 'producao'
        item.data_inicio_producao = agora
        item.usuario_producao_id = current_user.id
        # Atualiza pai se necessário
        if venda_pai.status == 'pendente':
            venda_pai.status = 'producao'
            venda_pai.data_inicio_producao = agora
            venda_pai.usuario_producao_id = current_user.id

    elif item.status == 'producao':
        item.status = 'pronto'
        item.data_pronto = agora
        item.usuario_pronto_id = current_user.id
        # Verifica se todos acabaram
        todos = ItemVenda.query.filter_by(venda_id=venda_pai.id).all()
        if all(i.status in ['pronto', 'entregue'] for i in todos):
            venda_pai.status = 'pronto'
            venda_pai.data_pronto = agora
            venda_pai.usuario_pronto_id = current_user.id

    db.session.commit()
    return redirect(url_for('operacional.painel'))

@bp_operacional.route('/item/<int:id>/voltar')
@login_required
@cargo_exigido('producao_operar')
def voltar_item(id):
    item = ItemVenda.query.get_or_404(id)
    if item.status == 'producao':
        item.status = 'pendente'
        item.data_inicio_producao = None
        item.usuario_producao_id = None
    elif item.status == 'pronto':
        item.status = 'producao'
        item.data_pronto = None
        item.usuario_pronto_id = None
    db.session.commit()
    return redirect(url_for('operacional.painel'))

# --- ROTAS DE AÇÃO PARA VENDAS SIMPLES ---

@bp_operacional.route('/venda/<int:id>/avancar')
@login_required
@cargo_exigido('producao_operar')
def avancar_venda(id):
    venda = Venda.query.get_or_404(id)
    agora = hora_brasilia()

    if venda.status == 'pendente':
        venda.status = 'producao'
        venda.data_inicio_producao = agora
        venda.usuario_producao_id = current_user.id
    elif venda.status == 'producao':
        venda.status = 'pronto'
        venda.data_pronto = agora
        venda.usuario_pronto_id = current_user.id
    
    db.session.commit()
    return redirect(url_for('operacional.painel'))

@bp_operacional.route('/venda/<int:id>/voltar')
@login_required
@cargo_exigido('producao_operar')
def voltar_venda(id):
    venda = Venda.query.get_or_404(id)
    if venda.status == 'producao':
        venda.status = 'pendente'
        venda.data_inicio_producao = None
        venda.usuario_producao_id = None
    elif venda.status == 'pronto':
        venda.status = 'producao'
        venda.data_pronto = None
        venda.usuario_pronto_id = None
    
    db.session.commit()
    return redirect(url_for('operacional.painel'))