from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from src.extensoes import banco_de_dados as db
from src.modulos.estoque import bp_estoque
from src.modulos.estoque.modelos import ProdutoEstoque, MovimentacaoEstoque
from src.modulos.estoque.formularios import FormularioProdutoEstoque, FormularioMovimentacaoManual
from src.modulos.autenticacao.permissoes import cargo_exigido

@bp_estoque.route('/', methods=['GET', 'POST'])
@login_required
@cargo_exigido('producao_operar') # Ou criar permissão 'estoque_gerir'
def painel():
    form_prod = FormularioProdutoEstoque()
    form_mov = FormularioMovimentacaoManual()
    
    # Adicionar Novo Produto
    if form_prod.validate_on_submit() and 'nome' in request.form:
        novo = ProdutoEstoque(
            nome=form_prod.nome.data,
            unidade=form_prod.unidade.data,
            estoque_minimo=form_prod.estoque_minimo.data or 0
        )
        db.session.add(novo)
        db.session.commit()
        flash('Produto criado com sucesso!', 'success')
        return redirect(url_for('estoque.painel'))

    produtos = ProdutoEstoque.query.filter_by(ativo=True).order_by(ProdutoEstoque.nome).all()
    
    return render_template('estoque/painel.html', produtos=produtos, form_prod=form_prod, form_mov=form_mov)

@bp_estoque.route('/movimentar/<int:id>', methods=['POST'])
@login_required
def movimentar_manual(id):
    produto = ProdutoEstoque.query.get_or_404(id)
    form = FormularioMovimentacaoManual()
    
    if form.validate_on_submit():
        qtd = form.quantidade.data
        tipo = form.tipo.data
        
        saldo_ant = produto.quantidade_atual
        
        if tipo == 'entrada':
            produto.quantidade_atual += qtd
        else:
            produto.quantidade_atual -= qtd
            
        mov = MovimentacaoEstoque(
            produto_id=produto.id,
            tipo=tipo,
            quantidade=qtd,
            saldo_anterior=saldo_ant,
            saldo_novo=produto.quantidade_atual,
            origem='manual',
            usuario_id=current_user.id,
            observacao=form.observacao.data
        )
        db.session.add(mov)
        db.session.commit()
        flash('Estoque atualizado.', 'success')
        
    return redirect(url_for('estoque.painel'))