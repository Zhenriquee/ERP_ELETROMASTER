from flask import redirect, url_for, request, flash
from flask_login import login_required, current_user
from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import ItemVenda, Venda, ItemVendaHistorico, hora_brasilia
from src.modulos.autenticacao.permissoes import cargo_exigido
from src.modulos.estoque.modelos import ProdutoEstoque, MovimentacaoEstoque
from decimal import Decimal
from . import bp_operacional

# --- NOVO: ROTA PARA ENVIAR PARA RETRABALHO (ITEM) ---
@bp_operacional.route('/item/<int:id>/retrabalho')
@login_required
@cargo_exigido('producao_operar')
def retrabalho_item(id):
    item = ItemVenda.query.get_or_404(id)
    venda_pai = Venda.query.get(item.venda_id)
    agora = hora_brasilia()
    
    status_anterior = item.status
    item.status = 'retrabalho'
    
    # Se não tiver data de inicio, define agora (caso raro)
    if not item.data_inicio_producao:
        item.data_inicio_producao = agora
    
    log = ItemVendaHistorico(
        item_id=item.id,
        usuario_id=current_user.id,
        status_anterior=status_anterior,
        status_novo='retrabalho',
        acao="Enviado para Retrabalho",
        data_acao=agora
    )
    db.session.add(log)
    
    # Atualiza status do Pai se necessário (se estava pronto, volta para produção)
    if venda_pai.modo == 'multipla':
        if venda_pai.status == 'pronto':
            venda_pai.status = 'producao'
            
    db.session.commit()
    flash('Item enviado para Retrabalho.', 'warning')
    return redirect(url_for('operacional.painel'))

# --- NOVO: ROTA PARA ENVIAR PARA RETRABALHO (VENDA SIMPLES) ---
@bp_operacional.route('/venda/<int:id>/retrabalho')
@login_required
@cargo_exigido('producao_operar')
def retrabalho_venda(id):
    venda = Venda.query.get_or_404(id)
    agora = hora_brasilia()
    
    status_anterior = venda.status
    venda.status = 'retrabalho'
    
    # Atualiza itens filhos
    if venda.itens:
        for item in venda.itens:
            item.status = 'retrabalho'
    
    # Log no primeiro item (para histórico)
    if venda.itens:
        log = ItemVendaHistorico(
            item_id=venda.itens[0].id,
            usuario_id=current_user.id,
            status_anterior=status_anterior,
            status_novo='retrabalho',
            acao="Venda Simples -> Retrabalho",
            data_acao=agora
        )
        db.session.add(log)

    db.session.commit()
    flash('Serviço enviado para Retrabalho.', 'warning')
    return redirect(url_for('operacional.painel'))

# --- ATUALIZAÇÃO: AVANÇAR ITEM (Aceita Produção ou Retrabalho -> Pronto) ---
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
        
    elif item.status in ['producao', 'retrabalho']: # <--- ALTERADO
        item.status = 'pronto'
        item.data_pronto = agora
        item.usuario_pronto_id = current_user.id
        acao_texto = "Finalizou Serviço"

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

    # Verifica status do pai
    todos_itens = ItemVenda.query.filter_by(venda_id=venda_pai.id).all()
    status_set = set(i.status for i in todos_itens)

    if all(s in ['pronto', 'entregue'] for s in status_set):
        if venda_pai.status not in ['pronto', 'entregue']:
            venda_pai.status = 'pronto'
            venda_pai.data_pronto = agora
            venda_pai.usuario_pronto_id = current_user.id
    elif 'producao' in status_set or 'retrabalho' in status_set:
        if venda_pai.status == 'pendente' or venda_pai.status == 'pronto':
            venda_pai.status = 'producao'
            if not venda_pai.data_inicio_producao:
                venda_pai.data_inicio_producao = agora
                venda_pai.usuario_producao_id = current_user.id

    db.session.commit()
    return redirect(url_for('operacional.painel'))

@bp_operacional.route('/item/<int:id>/voltar')
@login_required
@cargo_exigido('producao_operar')
def voltar_item(id):
    item = ItemVenda.query.get_or_404(id)
    venda_pai = Venda.query.get(item.venda_id)
    agora = hora_brasilia()
    
    status_anterior = item.status
    acao_texto = ""

    if item.status == 'producao':
        acao_texto = "Retornou para Fila (Desfez Início)"
        item.status = 'pendente'
        item.data_inicio_producao = None
        item.usuario_producao_id = None
        
    elif item.status == 'pronto':
        acao_texto = "Retornou para Produção (Correção)"
        item.status = 'producao'
        item.data_pronto = None
        item.usuario_pronto_id = None
        
        # Estorna baixas automáticas manuais se houver (opcional, mas seguro)
        movimentacoes = MovimentacaoEstoque.query.filter_by(
            referencia_id=item.id,
            origem='producao',
            tipo='saida'
        ).all()
        
        for mov in movimentacoes:
            prod = ProdutoEstoque.query.get(mov.produto_id)
            if prod:
                prod.quantidade_atual += mov.quantidade
            db.session.delete(mov)

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

    # Atualiza Pai
    todos_itens = ItemVenda.query.filter_by(venda_id=venda_pai.id).all()
    status_set = set(i.status for i in todos_itens)

    if 'producao' in status_set or 'retrabalho' in status_set:
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

# --- ATUALIZAÇÃO: AVANÇAR VENDA (Aceita Produção ou Retrabalho -> Pronto) ---
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
        if venda.itens:
            for item in venda.itens:
                item.status = 'producao'
                item.data_inicio_producao = agora
                item.usuario_producao_id = current_user.id

    elif venda.status in ['producao', 'retrabalho']: # <--- ALTERADO
        # Baixa Automática (Venda Simples)
        if venda.modo == 'simples' and venda.produto_id:
            produto = ProdutoEstoque.query.get(venda.produto_id)
            if produto:
                fator_consumo = Decimal(0)
                if venda.tipo_medida == 'm3':
                    fator_consumo = produto.consumo_por_m3 or Decimal(0)
                else:
                    fator_consumo = produto.consumo_por_m2 or Decimal(0)
                
                metragem = venda.metragem_total or Decimal(0)
                qtd_baixa = metragem * fator_consumo
                
                if qtd_baixa > 0:
                    mov = MovimentacaoEstoque(
                        produto_id=produto.id,
                        tipo='saida',
                        quantidade=qtd_baixa,
                        saldo_anterior=produto.quantidade_atual,
                        saldo_novo=produto.quantidade_atual - qtd_baixa,
                        origem='producao',
                        referencia_id=venda.itens[0].id if venda.itens else None, 
                        usuario_id=current_user.id,
                        observacao=f"Baixa Auto ({'Retrabalho' if venda.status=='retrabalho' else 'Normal'}) - #{venda.id}"
                    )
                    produto.quantidade_atual -= qtd_baixa
                    db.session.add(mov)
                    flash(f'Finalizado! Baixa de {qtd_baixa:.3f} {produto.unidade} registrada.', 'success')

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
    
    if venda.status in ['producao', 'retrabalho']:
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
                
                # Estorna baixas
                movimentacoes = MovimentacaoEstoque.query.filter_by(
                    referencia_id=item.id,
                    origem='producao',
                    tipo='saida'
                ).all()
                for mov in movimentacoes:
                    prod = ProdutoEstoque.query.get(mov.produto_id)
                    if prod:
                        prod.quantidade_atual += mov.quantidade
                    db.session.delete(mov)

    db.session.commit()
    return redirect(url_for('operacional.painel'))


@bp_operacional.route('/item/<int:id>/finalizar_com_baixa', methods=['POST'])
@login_required
def finalizar_com_baixa(id):
    item = ItemVenda.query.get_or_404(id)
    
    # Guarda status anterior para o log
    status_anterior = item.status 
    
    # Atualiza status para pronto
    item.status = 'pronto'
    item.data_pronto = hora_brasilia()
    item.usuario_pronto_id = current_user.id
    
    # Coleta dados do formulário
    produtos_ids = request.form.getlist('produtos_ids[]')
    quantidades = request.form.getlist('quantidades[]')
    
    consumo_texto = []
    total_debitado = 0

    for p_id, qtd_str in zip(produtos_ids, quantidades):
        if p_id and qtd_str:
            try:
                # Tratamento de número (Brasil -> Python)
                qtd_str_limpa = qtd_str.replace('.', '').replace(',', '.') if ',' in qtd_str and '.' in qtd_str else qtd_str.replace(',', '.')
                qtd = Decimal(qtd_str_limpa)
                
                if qtd > 0:
                    prod = ProdutoEstoque.query.get(int(p_id))
                    if prod:
                        # --- CORREÇÃO AQUI ---
                        # Removemos a divisão por 1000. 
                        # Agora o sistema respeita exatamente o que foi digitado.
                        qtd_baixa = qtd
                        unidade_log = prod.unidade
                        
                        # Cria movimentação
                        mov = MovimentacaoEstoque(
                            produto_id=prod.id,
                            tipo='saida',
                            quantidade=qtd_baixa,
                            saldo_anterior=prod.quantidade_atual,
                            saldo_novo=prod.quantidade_atual - qtd_baixa,
                            origem='producao', 
                            referencia_id=item.id, 
                            usuario_id=current_user.id,
                            observacao=f"Consumo Manual Item #{item.id} ({'Retrabalho' if status_anterior == 'retrabalho' else 'Produção'})"
                        )
                        
                        # Atualiza saldo
                        prod.quantidade_atual -= qtd_baixa
                        db.session.add(mov)
                        
                        consumo_texto.append(f"{qtd:.3f} {unidade_log} de {prod.nome}")
                        total_debitado += 1
            except ValueError:
                continue 

    # Gera Log
    acao_msg = "Finalizou Produção"
    if status_anterior == 'retrabalho':
        acao_msg = "Finalizou Retrabalho"
    
    detalhe_consumo = f"(Baixa: {', '.join(consumo_texto)})" if consumo_texto else "(Sem consumo extra informado)"
    
    log = ItemVendaHistorico(
        item_id=item.id,
        usuario_id=current_user.id,
        status_anterior=status_anterior,
        status_novo='pronto',
        acao=f"{acao_msg} {detalhe_consumo}",
        data_acao=hora_brasilia()
    )
    db.session.add(log)
    
    # Verifica status do Pai
    venda_pai = Venda.query.get(item.venda_id)
    todos_itens = ItemVenda.query.filter_by(venda_id=venda_pai.id).all()
    
    if all(i.status in ['pronto', 'entregue'] for i in todos_itens):
        if venda_pai.status not in ['pronto', 'entregue']:
            venda_pai.status = 'pronto'
            venda_pai.data_pronto = hora_brasilia()
            venda_pai.usuario_pronto_id = current_user.id
            
    db.session.commit()
    
    if total_debitado > 0:
        flash(f'Item finalizado! Estoque atualizado: {", ".join(consumo_texto)}.', 'success')
    else:
        flash('Item finalizado sem baixa de material.', 'info')
        
    return redirect(url_for('operacional.painel'))