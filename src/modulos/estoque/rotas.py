from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from src.extensoes import banco_de_dados as db
from src.modulos.estoque import bp_estoque
from src.modulos.estoque.modelos import ProdutoEstoque, MovimentacaoEstoque
from src.modulos.estoque.formularios import FormularioProdutoEstoque, FormularioMovimentacaoManual
from src.modulos.autenticacao.permissoes import cargo_exigido

@bp_estoque.route('/', methods=['GET', 'POST'])
@login_required
@cargo_exigido('estoque_gerir')
def painel():
    form_prod = FormularioProdutoEstoque()
    form_mov = FormularioMovimentacaoManual()
    
    # Adicionar Novo Produto
    if form_prod.validate_on_submit() and 'nome' in request.form:
        novo = ProdutoEstoque(
            nome=form_prod.nome.data,
            unidade=form_prod.unidade.data,
            quantidade_atual=form_prod.quantidade_atual.data or 0,
            
            # CAMPO ATUALIZADO AQUI:
            quantidade_minima=form_prod.quantidade_minima.data or 0,
            
            valor_unitario=form_prod.valor_unitario.data or 0,
            preco_m2=form_prod.preco_m2.data or 0,
            preco_m3=form_prod.preco_m3.data or 0,
            consumo_por_m2=form_prod.consumo_m2.data or 0,
            consumo_por_m3=form_prod.consumo_m3.data or 0
        )
        db.session.add(novo)
        db.session.commit()
        flash('Produto criado com sucesso!', 'success')
        return redirect(url_for('estoque.painel'))

    produtos = ProdutoEstoque.query.filter_by(ativo=True).order_by(ProdutoEstoque.nome).all()
    
    return render_template('estoque/painel.html', produtos=produtos, form_prod=form_prod, form_mov=form_mov)

@bp_estoque.route('/produto/editar/<int:id>', methods=['POST'])
@login_required
@cargo_exigido('estoque_gerir')
def editar_produto(id):
    produto = ProdutoEstoque.query.get_or_404(id)
    form = FormularioProdutoEstoque()
    
    if form.validate_on_submit():
        produto.nome = form.nome.data
        produto.unidade = form.unidade.data
        
        # CAMPO ATUALIZADO AQUI:
        produto.quantidade_minima = form.quantidade_minima.data
        
        produto.valor_unitario = form.valor_unitario.data
        produto.preco_m2 = form.preco_m2.data
        produto.preco_m3 = form.preco_m3.data
        produto.consumo_por_m2 = form.consumo_m2.data
        produto.consumo_por_m3 = form.consumo_m3.data
        
        # Atualiza quantidade se foi informada (opcional na edição)
        if form.quantidade_atual.data is not None:
             produto.quantidade_atual = form.quantidade_atual.data

        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
    else:
        flash('Erro ao atualizar produto. Verifique os campos.', 'error')
        
    return redirect(url_for('estoque.painel'))

# ... (Manter rotas de movimentar e histórico iguais ao anterior) ...
@bp_estoque.route('/movimentar/<int:id>', methods=['POST'])
@login_required
@cargo_exigido('estoque_gerir')
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

@bp_estoque.route('/api/historico/<int:id>', methods=['GET'])
@login_required
@cargo_exigido('estoque_gerir')
def api_historico_produto(id):
    movimentacoes = MovimentacaoEstoque.query.filter_by(produto_id=id).order_by(MovimentacaoEstoque.data_movimentacao.desc()).all()
    dados = []
    for mov in movimentacoes:
        dados.append({
            'id': mov.id,
            'data': mov.data_movimentacao.strftime('%d/%m/%Y %H:%M'),
            'tipo': mov.tipo,
            'quantidade': float(mov.quantidade),
            'saldo_novo': float(mov.saldo_novo) if mov.saldo_novo else 0,
            'origem': mov.origem,
            'observacao': mov.observacao or '-',
            'usuario': mov.usuario.nome if mov.usuario else 'Sistema'
        })
    return jsonify(dados)