from flask import redirect, url_for, flash
from flask_login import login_required
from datetime import date
from src.modulos.autenticacao.permissoes import cargo_exigido
from src.extensoes import banco_de_dados as db
from src.modulos.financeiro.modelos import Despesa
from src.modulos.estoque.modelos import MovimentacaoEstoque, ProdutoEstoque
from . import bp_financeiro

@bp_financeiro.route('/pagar/<int:id>')
@login_required
@cargo_exigido('financeiro_pagar')
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
@cargo_exigido('financeiro_excluir')
def excluir_despesa(id):
    despesa_alvo = Despesa.query.get_or_404(id)
    
    # Verifica se a conta faz parte de um grupo de parcelas
    if despesa_alvo.grupo_parcelamento:
        # Puxa todas as parcelas do mesmo grupo
        despesas_para_excluir = Despesa.query.filter_by(grupo_parcelamento=despesa_alvo.grupo_parcelamento).all()
    else:
        # Conta única
        despesas_para_excluir = [despesa_alvo]

    msg_estoque = ""
    
    # Processa a exclusão e o estorno para todas as contas vinculadas
    for despesa in despesas_para_excluir:
        # Verifica se alguma delas gerou entrada no estoque
        movimentacao = MovimentacaoEstoque.query.filter_by(
            referencia_id=despesa.id, 
            origem='compra'
        ).first()
        
        if movimentacao:
            produto = ProdutoEstoque.query.get(movimentacao.produto_id)
            if produto:
                produto.quantidade_atual -= movimentacao.quantidade
                msg_estoque = f" (O Estoque vinculado foi revertido automaticamente)"
            db.session.delete(movimentacao)

        # Exclui a despesa da tabela
        db.session.delete(despesa)
        
    db.session.commit()
    
    if len(despesas_para_excluir) > 1:
        flash(f'Lançamento e todas as suas {len(despesas_para_excluir)} parcelas foram excluídas{msg_estoque}.', 'info')
    else:
        flash(f'Lançamento excluído com sucesso{msg_estoque}.', 'info')
        
    return redirect(url_for('financeiro.painel'))