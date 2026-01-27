from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user
from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import ItemVenda, Venda, ItemVendaHistorico, hora_brasilia
from src.modulos.autenticacao.permissoes import cargo_exigido
from src.modulos.estoque.modelos import ProdutoEstoque, MovimentacaoEstoque
from decimal import Decimal


bp_operacional = Blueprint('operacional', __name__, url_prefix='/operacional')

@bp_operacional.route('/painel')
@login_required
@cargo_exigido('producao_operar')
def painel():
    
    # 1. Busca ITENS (CORREÇÃO: Adicionado filtro Venda.modo == 'multipla')
    # Isso impede que o item da venda simples apareça aqui duplicado, pois ele já será tratado na lista de vendas_simples abaixo.
    itens_multi = ItemVenda.query.join(Venda).filter(
        ItemVenda.status.in_(['pendente', 'producao', 'pronto']),
        Venda.status != 'cancelado',
        Venda.status != 'orcamento',
        Venda.modo == 'multipla'  # <--- LINHA NOVA: Filtra apenas itens de vendas múltiplas
    ).all()

    # 2. Busca VENDAS SIMPLES
    # Estas são tratadas como um "card único" no painel
    vendas_simples = Venda.query.filter(
        Venda.modo == 'simples',
        Venda.status.in_(['pendente', 'producao', 'pronto']),
        Venda.status != 'orcamento'
    ).all()

    tarefas = []

    # Processa Itens Individuais (de Vendas Múltiplas)
    for i in itens_multi:
        tarefas.append({
            'tipo': 'item',
            'id': i.id,
            'venda_id': i.venda_id,
            'descricao': i.descricao,
            'quantidade': i.quantidade,
            'cor': i.cor.nome,
            'status': i.status,
            'cliente': i.venda.cliente_nome,
            'obs': i.venda.observacoes_internas,
            'criado_em': i.venda.criado_em,
            'is_producao': (i.status == 'producao')
        })

    # Processa Vendas Simples (Card Unificado)
    for v in vendas_simples:
        tarefas.append({
            'tipo': 'venda',
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

    # Ordenação: Prioridade para quem está em produção, depois data de criação
    tarefas.sort(key=lambda x: (not x['is_producao'], x['criado_em']))

    # Contagem para os KPIs do topo
    qtd_fila = sum(1 for t in tarefas if t['status'] == 'pendente')
    qtd_producao = sum(1 for t in tarefas if t['status'] == 'producao')
    qtd_pronto = sum(1 for t in tarefas if t['status'] == 'pronto')
    produtos_estoque = ProdutoEstoque.query.filter_by(ativo=True).all()

    return render_template('operacional/painel.html', 
                           tarefas=tarefas,
                           qtd_fila=qtd_fila, 
                           qtd_producao=qtd_producao, 
                           qtd_pronto=qtd_pronto,
                           produtos_estoque=produtos_estoque)


# --- ROTA DE AVANÇAR (COM HISTÓRICO) ---
@bp_operacional.route('/item/<int:id>/avancar')
@login_required
@cargo_exigido('producao_operar')
def avancar_item(id):
    item = ItemVenda.query.get_or_404(id)
    venda_pai = Venda.query.get(item.venda_id)
    agora = hora_brasilia()
    
    status_anterior = item.status
    acao_texto = ""

    if item.status == 'pendente':
        item.status = 'producao'
        item.data_inicio_producao = agora
        item.usuario_producao_id = current_user.id
        acao_texto = "Iniciou Produção"
        
    elif item.status == 'producao':
        item.status = 'pronto'
        item.data_pronto = agora
        item.usuario_pronto_id = current_user.id
        acao_texto = "Finalizou Produção"

    # 1. Grava no Histórico
    if acao_texto:
        log = ItemVendaHistorico(
            item_id=item.id,
            usuario_id=current_user.id,
            status_anterior=status_anterior,
            status_novo=item.status,
            acao=acao_texto,
            data_acao=agora
        )
        db.session.add(log)

    # 2. Sincroniza Venda Pai
    todos_itens = ItemVenda.query.filter_by(venda_id=venda_pai.id).all()
    status_set = set(i.status for i in todos_itens)

    if all(s in ['pronto', 'entregue'] for s in status_set):
        if venda_pai.status != 'pronto' and venda_pai.status != 'entregue':
            venda_pai.status = 'pronto'
            venda_pai.data_pronto = agora
            venda_pai.usuario_pronto_id = current_user.id
    elif 'producao' in status_set:
        if venda_pai.status == 'pendente':
            venda_pai.status = 'producao'
            venda_pai.data_inicio_producao = agora
            venda_pai.usuario_producao_id = current_user.id
    elif status_set == {'pendente'}:
        venda_pai.status = 'pendente'

    db.session.commit()
    return redirect(url_for('operacional.painel'))


# --- ROTA DE VOLTAR (COM HISTÓRICO DE QUEM VOLTOU) ---
@bp_operacional.route('/item/<int:id>/voltar')
@login_required
@cargo_exigido('producao_operar')
def voltar_item(id):
    item = ItemVenda.query.get_or_404(id)
    venda_pai = Venda.query.get(item.venda_id)
    agora = hora_brasilia()
    
    status_anterior = item.status
    acao_texto = ""

    # 1. Define a ação de regressão
    if item.status == 'producao':
        acao_texto = "Retornou para Fila (Desfez Início)"
        item.status = 'pendente'
        item.data_inicio_producao = None
        item.usuario_producao_id = None
        
    elif item.status == 'pronto':
        acao_texto = "Retornou para Produção (Desfez Finalização)"
        item.status = 'producao'
        item.data_pronto = None
        item.usuario_pronto_id = None

    # 2. Salva o Log de Auditoria
    if acao_texto:
        log = ItemVendaHistorico(
            item_id=item.id,
            usuario_id=current_user.id,
            status_anterior=status_anterior,
            status_novo=item.status,
            acao=acao_texto,
            data_acao=agora
        )
        db.session.add(log)

    # 3. Sincroniza Venda Pai (Recálculo Reverso)
    todos_itens = ItemVenda.query.filter_by(venda_id=venda_pai.id).all()
    status_set = set(i.status for i in todos_itens)

    if 'producao' in status_set:
        venda_pai.status = 'producao'
    elif 'pendente' in status_set:
        if any(s in ['pronto', 'entregue'] for s in status_set):
            venda_pai.status = 'producao'
        else:
            venda_pai.status = 'pendente'
            venda_pai.data_inicio_producao = None
            venda_pai.usuario_producao_id = None
    elif all(s in ['pronto', 'entregue'] for s in status_set):
        if 'pronto' in status_set:
            venda_pai.status = 'pronto'
    
    db.session.commit()
    return redirect(url_for('operacional.painel'))


# --- ROTAS PARA VENDA SIMPLES (AVANÇAR/VOLTAR O CARD INTEIRO) ---
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
        
        # Opcional: Atualizar também o item único vinculado
        if venda.itens:
            for item in venda.itens:
                item.status = 'producao'
                item.data_inicio_producao = agora
                item.usuario_producao_id = current_user.id

    elif venda.status == 'producao':
        venda.status = 'pronto'
        venda.data_pronto = agora
        venda.usuario_pronto_id = current_user.id
        
        if venda.itens:
            for item in venda.itens:
                item.status = 'pronto'
                item.data_pronto = agora
                item.usuario_pronto_id = current_user.id

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
        
        if venda.itens:
            for item in venda.itens:
                item.status = 'pendente'
                item.data_inicio_producao = None
                item.usuario_producao_id = None

    elif venda.status == 'pronto':
        venda.status = 'producao'
        venda.data_pronto = None
        venda.usuario_pronto_id = None
        
        if venda.itens:
            for item in venda.itens:
                item.status = 'producao'
                item.data_pronto = None
                item.usuario_pronto_id = None

    db.session.commit()
    return redirect(url_for('operacional.painel'))

# Crie uma nova rota específica para finalizar com baixa
@bp_operacional.route('/item/<int:id>/finalizar_com_baixa', methods=['POST'])
@login_required
def finalizar_com_baixa(id):
    item = ItemVenda.query.get_or_404(id)
    
    # 1. Atualiza Status do Item (Código existente de 'avancar_item' adaptado)
    item.status = 'pronto'
    item.data_pronto = hora_brasilia()
    item.usuario_pronto_id = current_user.id
    
    # 2. Registra Baixa de Estoque (Múltiplos produtos possíveis)
    # O form enviará arrays: produtos[] e quantidades[]
    produtos_ids = request.form.getlist('produtos_ids[]')
    quantidades = request.form.getlist('quantidades[]')
    
    consumo_texto = []

    for p_id, qtd_str in zip(produtos_ids, quantidades):
        if p_id and qtd_str:
            try:
                qtd = Decimal(qtd_str.replace(',', '.'))
                if qtd > 0:
                    prod = ProdutoEstoque.query.get(int(p_id))
                    
                    # Registra Movimentação
                    mov = MovimentacaoEstoque(
                        produto_id=prod.id,
                        tipo='saida',
                        quantidade=qtd,
                        saldo_anterior=prod.quantidade_atual,
                        saldo_novo=prod.quantidade_atual - qtd,
                        origem='producao',
                        referencia_id=item.id,
                        usuario_id=current_user.id,
                        observacao=f"Produção Item #{item.id} - {item.descricao}"
                    )
                    prod.quantidade_atual -= qtd
                    db.session.add(mov)
                    consumo_texto.append(f"{qtd} {prod.unidade} de {prod.nome}")
            except ValueError:
                pass # Ignora valores inválidos

    # 3. Log de Histórico
    log = ItemVendaHistorico(
        item_id=item.id,
        usuario_id=current_user.id,
        status_anterior='producao',
        status_novo='pronto',
        acao=f"Finalizou (Baixa: {', '.join(consumo_texto)})" if consumo_texto else "Finalizou Produção",
        data_acao=hora_brasilia()
    )
    db.session.add(log)
    
    # ... (Lógica de sincronizar Venda Pai) ...
    
    db.session.commit()
    return redirect(url_for('operacional.painel'))