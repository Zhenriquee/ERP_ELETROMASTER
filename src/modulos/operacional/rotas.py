from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import ItemVenda, Venda, ItemVendaHistorico, hora_brasilia # Adicionado ItemVendaHistorico
from src.modulos.autenticacao.permissoes import cargo_exigido

bp_operacional = Blueprint('operacional', __name__, url_prefix='/operacional')

@bp_operacional.route('/painel')
@login_required
@cargo_exigido('producao_operar')
def painel():
    # ... (Mantenha a lógica de busca e tarefas da resposta anterior inalterada) ...
    # Para economizar espaço aqui, estou focando nas rotas de ação abaixo.
    # Se precisar do código do painel novamente, me avise.
    
    # 1. Busca ITENS
    itens_multi = ItemVenda.query.join(Venda).filter(
        ItemVenda.status.in_(['pendente', 'producao', 'pronto']),
        Venda.status != 'cancelado',
        Venda.status != 'orcamento'
    ).all()

    # 2. Busca VENDAS SIMPLES
    vendas_simples = Venda.query.filter(
        Venda.modo == 'simples',
        Venda.status.in_(['pendente', 'producao', 'pronto']),
        Venda.status != 'orcamento'
    ).all()

    tarefas = []

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

    tarefas.sort(key=lambda x: (not x['is_producao'], x['criado_em']))

    qtd_fila = sum(1 for t in tarefas if t['status'] == 'pendente')
    qtd_producao = sum(1 for t in tarefas if t['status'] == 'producao')
    qtd_pronto = sum(1 for t in tarefas if t['status'] == 'pronto')

    return render_template('operacional/painel.html', 
                           tarefas=tarefas,
                           qtd_fila=qtd_fila, 
                           qtd_producao=qtd_producao, 
                           qtd_pronto=qtd_pronto)


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

    # 2. Sincroniza Venda Pai (Lógica mantida)
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
        # GRAVA O HISTÓRICO ANTES DE LIMPAR OS DADOS
        acao_texto = "Retornou para Fila (Desfez Início)"
        
        # Reseta o item
        item.status = 'pendente'
        item.data_inicio_producao = None
        item.usuario_producao_id = None
        
    elif item.status == 'pronto':
        # GRAVA O HISTÓRICO ANTES DE LIMPAR OS DADOS
        acao_texto = "Retornou para Produção (Desfez Finalização)"
        
        # Reseta o item (volta para producao)
        item.status = 'producao'
        item.data_pronto = None
        item.usuario_pronto_id = None

    # 2. Salva o Log de Auditoria
    if acao_texto:
        log = ItemVendaHistorico(
            item_id=item.id,
            usuario_id=current_user.id, # AQUI FICA REGISTRADO QUEM VOLTOU O PROCESSO
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

# ... (Rotas de venda simples mantidas iguais, ou pode adicionar lógica similar se quiser) ...
@bp_operacional.route('/venda/<int:id>/avancar')
def avancar_venda(id):
    # Lógica simplificada para Venda Simples (não tem tabela de historico de itens vinculada diretamente ainda)
    # Se quiser rastrear vendas simples, precisaria de uma tabela VendaHistorico similar.
    # Por enquanto, mantendo o original:
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