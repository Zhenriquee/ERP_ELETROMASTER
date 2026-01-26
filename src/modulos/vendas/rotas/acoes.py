from flask import redirect, url_for, flash, request
from flask_login import login_required, current_user
from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import Venda,  hora_brasilia, ItemVenda, ItemVendaHistorico
from . import bp_vendas

@bp_vendas.route('/servicos/<int:id>/status/<novo_status>')
@login_required
def mudar_status(id, novo_status):
    venda = Venda.query.get_or_404(id)
    agora = hora_brasilia()
    mapa_status = {'producao': 'Em Produção', 'pronto': 'Pronto', 'entregue': 'Entregue'}
    
    if novo_status in mapa_status:
        venda.status = novo_status
        if novo_status == 'producao':
            venda.data_inicio_producao = agora
            venda.usuario_producao_id = current_user.id
        elif novo_status == 'pronto':
            venda.data_pronto = agora
            venda.usuario_pronto_id = current_user.id
        elif novo_status == 'entregue':
            venda.data_entrega = agora
            venda.usuario_entrega_id = current_user.id

        if venda.modo == 'multipla':
            for item in venda.itens:
                if item.status != novo_status:
                    status_antigo = item.status
                    item.status = novo_status
                    if novo_status == 'producao':
                        item.data_inicio_producao = agora
                        item.usuario_producao_id = current_user.id
                    elif novo_status == 'pronto':
                        item.data_pronto = agora
                        item.usuario_pronto_id = current_user.id
                    elif novo_status == 'entregue':
                        item.data_entregue = agora
                        item.usuario_entrega_id = current_user.id
                    
                    log = ItemVendaHistorico(
                        item_id=item.id,
                        usuario_id=current_user.id,
                        status_anterior=status_antigo,
                        status_novo=novo_status,
                        acao=f"Ação em Massa ({mapa_status[novo_status]})",
                        data_acao=agora
                    )
                    db.session.add(log)

        db.session.commit()
        flash(f'Status atualizado para: {mapa_status[novo_status]}', 'success')
    
    return redirect(url_for('vendas.listar_vendas'))

@bp_vendas.route('/itens/<int:id>/status/<novo_status>')
@login_required
def mudar_status_item(id, novo_status):
    item = ItemVenda.query.get_or_404(id)
    venda_pai = Venda.query.get(item.venda_id)
    agora = hora_brasilia()
    
    mapa_status = {'pendente': 'Pendente', 'producao': 'Em Produção', 'pronto': 'Pronto', 'entregue': 'Entregue'}
    
    if novo_status in mapa_status:
        item.status = novo_status
        if novo_status == 'producao':
            item.data_inicio_producao = agora
            item.usuario_producao_id = current_user.id
        elif novo_status == 'pronto':
            item.data_pronto = agora
            item.usuario_pronto_id = current_user.id
        elif novo_status == 'entregue':
            item.data_entregue = agora
            item.usuario_entrega_id = current_user.id
            
        todos_itens = ItemVenda.query.filter_by(venda_id=venda_pai.id).all()
        status_set = set(i.status for i in todos_itens)
        
        if status_set == {'entregue'}:
            if venda_pai.status != 'entregue':
                venda_pai.status = 'entregue'
                venda_pai.data_entrega = agora
                venda_pai.usuario_entrega_id = current_user.id
        elif all(s in ['pronto', 'entregue'] for s in status_set):
            if venda_pai.status != 'pronto':
                venda_pai.status = 'pronto'
                venda_pai.data_pronto = agora
                venda_pai.usuario_pronto_id = current_user.id
        elif 'producao' in status_set or 'pronto' in status_set or 'entregue' in status_set:
            if venda_pai.status == 'pendente':
                venda_pai.status = 'producao'
                venda_pai.data_inicio_producao = agora
                venda_pai.usuario_producao_id = current_user.id

        db.session.commit()
        flash(f'Item atualizado.', 'success')
    
    return redirect(url_for('vendas.listar_vendas'))

@bp_vendas.route('/servicos/<int:id>/cancelar', methods=['POST'])
@login_required
def cancelar_venda(id):
    venda = Venda.query.get_or_404(id)
    if venda.status == 'entregue' and venda.valor_restante <= 0.01:
        flash('Não é possível cancelar um serviço finalizado e pago.', 'error')
        return redirect(url_for('vendas.listar_vendas'))
        
    motivo = request.form.get('motivo_cancelamento')
    if not motivo or len(motivo.strip()) < 5:
        flash('Informe o motivo (min 5 chars).', 'error')
        return redirect(url_for('vendas.listar_vendas'))
    
    venda.status = 'cancelado'
    venda.motivo_cancelamento = motivo
    venda.data_cancelamento = hora_brasilia()
    venda.usuario_cancelamento_id = current_user.id
    
    db.session.commit()
    flash('Serviço cancelado.', 'info')
    
    return redirect(url_for('vendas.listar_vendas'))