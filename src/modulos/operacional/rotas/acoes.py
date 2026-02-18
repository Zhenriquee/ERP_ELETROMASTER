from flask import redirect, url_for, request, flash
from flask_login import login_required, current_user
from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import ItemVenda, Venda, ItemVendaHistorico, hora_brasilia
from src.modulos.autenticacao.permissoes import cargo_exigido
from src.modulos.estoque.modelos import ProdutoEstoque, MovimentacaoEstoque
from decimal import Decimal
from . import bp_operacional

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

    elif venda.status == 'producao':
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
                        observacao=f"Baixa Automática - Venda #{venda.id} ({metragem} {venda.tipo_medida})"
                    )
                    produto.quantidade_atual -= qtd_baixa
                    db.session.add(mov)
                    flash(f'Serviço finalizado! Baixa automática de {qtd_baixa:.3f} {produto.unidade} registrada.', 'success')
                else:
                    flash('Serviço finalizado. Nenhuma baixa de estoque necessária.', 'info')

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
    item.status = 'pronto'
    item.data_pronto = hora_brasilia()
    item.usuario_pronto_id = current_user.id
    
    produtos_ids = request.form.getlist('produtos_ids[]')
    quantidades = request.form.getlist('quantidades[]')
    consumo_texto = []

    for p_id, qtd_str in zip(produtos_ids, quantidades):
        if p_id and qtd_str:
            try:
                qtd = Decimal(qtd_str.replace(',', '.'))
                if qtd > 0:
                    prod = ProdutoEstoque.query.get(int(p_id))
                    if prod:
                        qtd_baixa = qtd
                        if prod.unidade == 'KG':
                            qtd_baixa = qtd / 1000 
                        
                        mov = MovimentacaoEstoque(
                            produto_id=prod.id,
                            tipo='saida',
                            quantidade=qtd_baixa,
                            saldo_anterior=prod.quantidade_atual,
                            saldo_novo=prod.quantidade_atual - qtd_baixa,
                            origem='producao',
                            referencia_id=item.id,
                            usuario_id=current_user.id,
                            observacao=f"Produção Manual #{item.id} ({qtd}g)"
                        )
                        prod.quantidade_atual -= qtd_baixa
                        db.session.add(mov)
                        consumo_texto.append(f"{qtd}g de {prod.nome}")
            except ValueError:
                pass 

    log = ItemVendaHistorico(
        item_id=item.id,
        usuario_id=current_user.id,
        status_anterior='producao',
        status_novo='pronto',
        acao=f"Finalizou (Baixa Manual: {', '.join(consumo_texto)})" if consumo_texto else "Finalizou Produção (Sem baixa)",
        data_acao=hora_brasilia()
    )
    db.session.add(log)
    
    venda_pai = Venda.query.get(item.venda_id)
    todos_itens = ItemVenda.query.filter_by(venda_id=venda_pai.id).all()
    status_set = set(i.status for i in todos_itens)

    if all(s in ['pronto', 'entregue'] for s in status_set):
        if venda_pai.status != 'pronto' and venda_pai.status != 'entregue':
            venda_pai.status = 'pronto'
            venda_pai.data_pronto = hora_brasilia()
            venda_pai.usuario_pronto_id = current_user.id
            
    db.session.commit()
    flash(f'Item finalizado com sucesso! Consumo registrado.', 'success')
    return redirect(url_for('operacional.painel'))