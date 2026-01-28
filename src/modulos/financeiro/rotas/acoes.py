from flask import redirect, url_for, flash
from flask_login import login_required
from datetime import date

from src.extensoes import banco_de_dados as db
from src.modulos.financeiro.modelos import Despesa
from src.modulos.estoque.modelos import MovimentacaoEstoque, ProdutoEstoque
from . import bp_financeiro

@bp_financeiro.route('/pagar/<int:id>')
@login_required
def marcar_pago(id):
    despesa = Despesa.query.get_or_404(id)
    
    if despesa.status != 'pago':
        despesa.status = 'pago'
        despesa.data_pagamento = date.today()
        db.session.commit()
        flash('Conta marcada como PAGA.', 'success')
    
    return redirect(url_for('financeiro.painel'))

@bp_financeiro.route('/excluir/<int:id>')
@login_required
def excluir_despesa(id):
    despesa = Despesa.query.get_or_404(id)
    
    # --- LOGICA DE ESTORNO DE ESTOQUE ---
    # Verifica se essa despesa gerou uma entrada no estoque (compra vinculada)
    movimentacao = MovimentacaoEstoque.query.filter_by(
        referencia_id=despesa.id, 
        origem='compra'
    ).first()
    
    msg_estoque = ""
    
    if movimentacao:
        # Recupera o produto para abater o saldo
        produto = ProdutoEstoque.query.get(movimentacao.produto_id)
        if produto:
            # Reverte a entrada (Subtrai o que foi adicionado incorretamente)
            produto.quantidade_atual -= movimentacao.quantidade
            msg_estoque = f" (Estoque de {produto.nome} revertido)"
            
        # Deleta o registro de movimentação da tabela de estoque
        db.session.delete(movimentacao)

    # Exclui a despesa financeira
    db.session.delete(despesa)
    db.session.commit()
    
    flash(f'Lançamento excluído com sucesso{msg_estoque}.', 'info')
    return redirect(url_for('financeiro.painel'))