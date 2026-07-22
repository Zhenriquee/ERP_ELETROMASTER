from flask import redirect, url_for, request, flash
from flask_login import login_required, current_user
from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import ItemVenda, Venda, ItemVendaHistorico, hora_brasilia
from src.modulos.autenticacao.permissoes import cargo_exigido
from src.modulos.estoque.modelos import ProdutoEstoque, MovimentacaoEstoque
from decimal import Decimal
from . import bp_operacional

# --- FUNÇÃO AUXILIAR PARA ESTORNO GARANTIDO ---
def estornar_estoque_producao(referencia_id):
    """Remove a movimentação de saída e devolve a quantidade ao saldo do produto"""
    movimentacoes = MovimentacaoEstoque.query.filter_by(
        referencia_id=referencia_id,
        origem='producao',
        tipo='saida'
    ).all()
    
    qtd_estornada = 0
    for mov in movimentacoes:
        prod = ProdutoEstoque.query.get(mov.produto_id)
        if prod:
            prod.quantidade_atual += mov.quantidade
            db.session.add(prod) # Força a atualização do saldo
        db.session.delete(mov)   # Exclui o lançamento do histórico
        qtd_estornada += 1
        
    return qtd_estornada

# --- FUNÇÃO AUXILIAR: AGRUPAR ITENS FRAGMENTADOS ---
def agrupar_itens_fragmentados(item_id):
    """
    Busca se há outros itens na MESMA venda, com a MESMA descrição, 
    MESMO produto, MESMA cor e MESMO status.
    Se houver, mescla-os no item atual para evitar cards duplicados no painel
    quando pedaços separados de um lote (retrabalho parcial) terminam no mesmo estágio.
    """
    item = ItemVenda.query.get(item_id)
    if not item: return
    
    similares = ItemVenda.query.filter_by(
        venda_id=item.venda_id,
        status=item.status,
        descricao=item.descricao,
        produto_id=item.produto_id,
        cor_id=item.cor_id,
        tipo_medida=item.tipo_medida
    ).filter(ItemVenda.id != item.id).all()
    
    for outro in similares:
        item.quantidade += outro.quantidade
        item.valor_total += outro.valor_total
        if item.metragem_total and outro.metragem_total:
            item.metragem_total += outro.metragem_total
        elif outro.metragem_total:
            item.metragem_total = outro.metragem_total
            
        if outro.fotos:
            for foto in outro.fotos:
                foto.item_venda_id = item.id
                
        historicos = ItemVendaHistorico.query.filter_by(item_id=outro.id).all()
        for hist in historicos:
            hist.item_id = item.id
            
        # Reatribuir movimentações de estoque (para não perder o rastro do fragmento excluído)
        movimentacoes = MovimentacaoEstoque.query.filter_by(referencia_id=outro.id, origem='producao').all()
        for mov in movimentacoes:
            mov.referencia_id = item.id
            
        db.session.delete(outro)
    
    if similares:
        db.session.flush()

# --- ROTA PARA ENVIAR PARA RETRABALHO (ITEM) ---
@bp_operacional.route('/item/<int:id>/retrabalho', methods=['GET', 'POST'])
@login_required
@cargo_exigido('producao_operar')
def retrabalho_item(id):
    item = ItemVenda.query.get_or_404(id)
    venda_pai = Venda.query.get(item.venda_id)
    agora = hora_brasilia()
    
    status_anterior = item.status
    
    qtd_retrabalho = item.quantidade
    if request.method == 'POST':
        qtd_informada = request.form.get('quantidade_retrabalho', type=int)
        if qtd_informada and qtd_informada > 0 and qtd_informada <= item.quantidade:
            qtd_retrabalho = qtd_informada

    # Se a quantidade informada for menor que a total, faremos a DIVISÃO do item
    if qtd_retrabalho < item.quantidade:
        # Calcular proporções
        proporcao = Decimal(qtd_retrabalho) / Decimal(item.quantidade)
        valor_retrabalho = item.valor_total * proporcao
        metragem_retrabalho = (item.metragem_total or Decimal(0)) * proporcao
        
        # Subtrair do item original (mantém o status atual dele, ex: pronto ou producao)
        item.quantidade -= qtd_retrabalho
        item.valor_total -= valor_retrabalho
        if item.metragem_total:
            item.metragem_total -= metragem_retrabalho
            
        # Criar o novo item (clone para o retrabalho)
        novo_item = ItemVenda(
            venda_id=item.venda_id,
            descricao=item.descricao,
            cor_id=item.cor_id,
            produto_id=item.produto_id,
            quantidade=qtd_retrabalho,
            valor_unitario=item.valor_unitario,
            valor_total=valor_retrabalho,
            metragem_total=metragem_retrabalho,
            tipo_medida=item.tipo_medida,
            status='retrabalho',
            data_inicio_producao=agora,
            usuario_producao_id=item.usuario_producao_id or current_user.id
        )
        db.session.add(novo_item)
        db.session.flush() # Para gerar o ID do novo item
        
        # Copiar fotos do item original para o novo item
        if item.fotos:
            for foto in item.fotos:
                nova_foto = FotoItemVenda(
                    item_venda_id=novo_item.id,
                    nome_arquivo=foto.nome_arquivo,
                    tipo_mime=foto.tipo_mime,
                    dados_binarios=foto.dados_binarios,
                    etapa=foto.etapa,
                    enviado_por_id=foto.enviado_por_id,
                    data_upload=foto.data_upload
                )
                db.session.add(nova_foto)
                
        # O log de histórico vai para o novo item
        log = ItemVendaHistorico(
            item_id=novo_item.id,
            usuario_id=current_user.id,
            status_anterior=status_anterior,
            status_novo='retrabalho',
            acao=f"Retrabalho Parcial ({qtd_retrabalho} peças separadas)",
            data_acao=agora
        )
        db.session.add(log)
        
        # CORREÇÃO DE ESTOQUE para retrabalho parcial vindo de 'pronto':
        # O item restante PERMANECE 'pronto'. Apenas o estorno proporcional à fração
        # que foi para retrabalho é realizado:
        #   1. Estorna TODA a baixa original (que foi pelo total)
        #   2. Registra uma nova baixa apenas pelo restante (item.quantidade já reduzido)
        if status_anterior == 'pronto':
            # 1. Estorna o lançamento original (total)
            estornar_estoque_producao(item.id)

            # 2. Re-aplica a baixa apenas para a quantidade restante (que fica pronto)
            venda_pai_local = Venda.query.get(item.venda_id)
            if venda_pai_local and venda_pai_local.modo == 'simples' and venda_pai_local.produto_id:
                produto_est = ProdutoEstoque.query.get(venda_pai_local.produto_id)
                if produto_est:
                    fator = produto_est.consumo_por_m3 or Decimal(0) if venda_pai_local.tipo_medida == 'm3' else produto_est.consumo_por_m2 or Decimal(0)
                    metragem_total_venda = venda_pai_local.metragem_total or Decimal(0)
                    qtd_total_venda = Decimal(venda_pai_local.quantidade_pecas or 1)
                    metragem_restante = (metragem_total_venda / qtd_total_venda) * Decimal(item.quantidade)
                    qtd_nova_baixa = metragem_restante * fator
                    if qtd_nova_baixa > 0:
                        mov_novo = MovimentacaoEstoque(
                            produto_id=produto_est.id,
                            tipo='saida',
                            quantidade=qtd_nova_baixa,
                            saldo_anterior=produto_est.quantidade_atual,
                            saldo_novo=produto_est.quantidade_atual - qtd_nova_baixa,
                            origem='producao',
                            referencia_id=item.id,
                            usuario_id=current_user.id,
                            observacao=f"Reajuste Baixa Parcial (retrabalho) - Item #{item.id}"
                        )
                        produto_est.quantidade_atual -= qtd_nova_baixa
                        db.session.add(mov_novo)

            # O item restante FICA em 'pronto' — não volta para produção
            # Apenas garante que data_pronto continua preenchida
            flash(f'{qtd_retrabalho} peças enviadas para Retrabalho. As demais permanecem como Finalizadas.', 'warning')
        else:
            flash(f'{qtd_retrabalho} peças separadas para Retrabalho.', 'warning')
            
    else:
        # Lógica original para o item todo
        item.status = 'retrabalho'
        
        if status_anterior == 'pronto':
            estornar_estoque_producao(item.id)
            item.data_pronto = None
            item.usuario_pronto_id = None
        
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
        flash('Item enviado para Retrabalho.', 'warning')
    
    # Atualiza o status da Venda Pai se necessário
    if venda_pai.status == 'pronto':
        venda_pai.status = 'producao'
            
    db.session.flush()
    agrupar_itens_fragmentados(item.id)
    db.session.commit()
    return redirect(url_for('operacional.painel'))

# --- ROTA PARA ENVIAR PARA RETRABALHO (VENDA SIMPLES) ---
@bp_operacional.route('/venda/<int:id>/retrabalho')
@login_required
@cargo_exigido('producao_operar')
def retrabalho_venda(id):
    venda = Venda.query.get_or_404(id)
    agora = hora_brasilia()
    
    status_anterior = venda.status
    venda.status = 'retrabalho'
    
    if venda.itens:
        for item in venda.itens:
            # CORREÇÃO: Se estava pronto, estorna o estoque antes de voltar
            if status_anterior == 'pronto' or item.status == 'pronto':
                estornar_estoque_producao(item.id)
                item.data_pronto = None
                item.usuario_pronto_id = None
                
            item.status = 'retrabalho'
    
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

# --- AVANÇAR ITEM ---
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
        
    elif item.status in ['producao', 'retrabalho']:
        # Baixa de Estoque Automática (Venda Simples)
        if venda_pai.modo == 'simples' and venda_pai.produto_id:
            produto = ProdutoEstoque.query.get(venda_pai.produto_id)
            if produto:
                fator_consumo = Decimal(0)
                if venda_pai.tipo_medida == 'm3':
                    fator_consumo = produto.consumo_por_m3 or Decimal(0)
                else:
                    fator_consumo = produto.consumo_por_m2 or Decimal(0)
                
                # Calcula a metragem proporcional à quantidade DESSA parte do item dividido
                metragem_total_venda = venda_pai.metragem_total or Decimal(0)
                metragem_proporcional = (metragem_total_venda / Decimal(venda_pai.quantidade_pecas or 1)) * Decimal(item.quantidade)
                
                qtd_baixa = metragem_proporcional * fator_consumo
                
                if qtd_baixa > 0:
                    mov = MovimentacaoEstoque(
                        produto_id=produto.id,
                        tipo='saida',
                        quantidade=qtd_baixa,
                        saldo_anterior=produto.quantidade_atual,
                        saldo_novo=produto.quantidade_atual - qtd_baixa,
                        origem='producao',
                        referencia_id=item.id,
                        usuario_id=current_user.id,
                        observacao=f"Baixa Auto ({'Retrabalho' if item.status=='retrabalho' else 'Normal'}) - Item #{item.id}"
                    )
                    produto.quantidade_atual -= qtd_baixa
                    db.session.add(mov)
                    flash(f'Finalizado! Baixa proporcional de {qtd_baixa:.3f} {produto.unidade} registrada.', 'success')

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

    db.session.flush()
    agrupar_itens_fragmentados(item.id)
    db.session.commit()
    return redirect(url_for('operacional.painel'))

# --- VOLTAR ITEM ---
@bp_operacional.route('/item/<int:id>/voltar')
@login_required
@cargo_exigido('producao_operar')
def voltar_item(id):
    item = ItemVenda.query.get_or_404(id)
    venda_pai = Venda.query.get(item.venda_id)
    agora = hora_brasilia()
    
    status_anterior = item.status
    acao_texto = ""
    qtd_estornada = 0

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
        
        # O ESTORNO GARANTIDO ACONTECE AQUI!
        qtd_estornada = estornar_estoque_producao(item.id)

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
    
    db.session.flush()
    agrupar_itens_fragmentados(item.id)
    db.session.commit()
    
    # Feedback visual claro para o usuário
    if qtd_estornada > 0:
        flash(f'Item retornado à produção. {qtd_estornada} baixa(s) de estoque revertida(s) com sucesso!', 'success')
    else:
        flash('Item retornado à produção.', 'info')
        
    return redirect(url_for('operacional.painel'))

# --- AVANÇAR VENDA ---
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

    elif venda.status in ['producao', 'retrabalho']:
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

# --- VOLTAR VENDA ---
@bp_operacional.route('/venda/<int:id>/voltar')
@login_required
@cargo_exigido('producao_operar')
def voltar_venda(id):
    venda = Venda.query.get_or_404(id)
    qtd_estornada = 0
    
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
                
                # ESTORNO GARANTIDO
                qtd_estornada += estornar_estoque_producao(item.id)

    db.session.commit()
    
    if qtd_estornada > 0:
        flash(f'Serviço retornado à produção. {qtd_estornada} baixa(s) de estoque revertida(s) com sucesso.', 'success')
    else:
        flash('Serviço retornado para fila/produção.', 'info')
        
    return redirect(url_for('operacional.painel'))

# --- FINALIZAR COM BAIXA (ITEM MULTIPLO) ---
@bp_operacional.route('/item/<int:id>/finalizar_com_baixa', methods=['POST'])
@login_required
def finalizar_com_baixa(id):
    item = ItemVenda.query.get_or_404(id)
    status_anterior = item.status 
    
    item.status = 'pronto'
    item.data_pronto = hora_brasilia()
    item.usuario_pronto_id = current_user.id
    
    produtos_ids = request.form.getlist('produtos_ids[]')
    quantidades = request.form.getlist('quantidades[]')
    
    consumo_texto = []
    total_debitado = 0

    for p_id, qtd_str in zip(produtos_ids, quantidades):
        if p_id and qtd_str:
            try:
                qtd_str_limpa = qtd_str.replace('.', '').replace(',', '.') if ',' in qtd_str and '.' in qtd_str else qtd_str.replace(',', '.')
                qtd = Decimal(qtd_str_limpa)
                
                if qtd > 0:
                    prod = ProdutoEstoque.query.get(int(p_id))
                    if prod:
                        qtd_baixa = qtd
                        unidade_log = prod.unidade
                        
                        mov = MovimentacaoEstoque(
                            produto_id=prod.id,
                            tipo='saida',
                            quantidade=qtd_baixa,
                            saldo_anterior=prod.quantidade_atual,
                            saldo_novo=prod.quantidade_atual - qtd_baixa,
                            origem='producao', 
                            referencia_id=item.id, 
                            usuario_id=current_user.id,
                            observacao=f"Consumo Item #{item.id} ({'Retrabalho' if status_anterior == 'retrabalho' else 'Produção'})"
                        )
                        
                        prod.quantidade_atual -= qtd_baixa
                        db.session.add(mov)
                        
                        consumo_texto.append(f"{qtd:.3f} {unidade_log} de {prod.nome}")
                        total_debitado += 1
            except ValueError:
                continue 

    acao_msg = "Finalizou Produção"
    if status_anterior == 'retrabalho':
        acao_msg = "Finalizou Retrabalho"
    
    detalhe_consumo = f"(Baixa: {', '.join(consumo_texto)})" if consumo_texto else "(Sem consumo extra informado)"
    
    # SEGURANÇA: Truncar a mensagem para não estourar o limite de 255 do banco de dados
    acao_completa = f"{acao_msg} {detalhe_consumo}"
    if len(acao_completa) > 250:
        acao_completa = acao_completa[:247] + "..."
    
    log = ItemVendaHistorico(
        item_id=item.id,
        usuario_id=current_user.id,
        status_anterior=status_anterior,
        status_novo='pronto',
        acao=acao_completa,
        data_acao=hora_brasilia()
    )
    db.session.add(log)
    
    venda_pai = Venda.query.get(item.venda_id)
    todos_itens = ItemVenda.query.filter_by(venda_id=venda_pai.id).all()
    
    if all(i.status in ['pronto', 'entregue'] for i in todos_itens):
        if venda_pai.status not in ['pronto', 'entregue']:
            venda_pai.status = 'pronto'
            venda_pai.data_pronto = hora_brasilia()
            venda_pai.usuario_pronto_id = current_user.id
            
    db.session.flush()
    agrupar_itens_fragmentados(item.id)
    db.session.commit()
    
    if total_debitado > 0:
        flash(f'Item finalizado! Estoque atualizado: {", ".join(consumo_texto)}.', 'success')
    else:
        flash('Item finalizado sem baixa de material.', 'info')
        
    return redirect(url_for('operacional.painel'))