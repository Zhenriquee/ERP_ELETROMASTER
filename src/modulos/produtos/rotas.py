from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from src.extensoes import banco_de_dados as db
# Importamos os modelos que ainda estão na pasta vendas (por enquanto)
from src.modulos.vendas.modelos import CorServico, HistoricoPrecoCor
from src.modulos.produtos.formularios import FormularioProduto

bp_produtos = Blueprint('produtos', __name__, url_prefix='/produtos')

@bp_produtos.route('/', methods=['GET', 'POST'])
@login_required
def gerenciar():
    form = FormularioProduto()
    
    if form.validate_on_submit():
        nova_cor = CorServico(
            nome=form.nome.data,
            unidade_medida=form.unidade.data,
            preco_unitario=form.preco.data,
            ativo=True
        )
        db.session.add(nova_cor)
        db.session.commit()
        
        # Log de Governança
        log = HistoricoPrecoCor(
            cor_id=nova_cor.id,
            preco_anterior=0,
            preco_novo=form.preco.data,
            usuario_id=current_user.id
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Produto cadastrado com sucesso!', 'success')
        return redirect(url_for('produtos.gerenciar'))

    produtos = CorServico.query.order_by(CorServico.ativo.desc(), CorServico.nome).all()
    return render_template('produtos/gerenciar.html', form=form, produtos=produtos)

@bp_produtos.route('/editar/<int:id>', methods=['POST'])
@login_required
def editar(id):
    produto = CorServico.query.get_or_404(id)
    form = FormularioProduto()

    if form.validate_on_submit():
        preco_antigo = produto.preco_unitario
        novo_preco = form.preco.data

        produto.nome = form.nome.data
        produto.unidade_medida = form.unidade.data
        produto.preco_unitario = novo_preco

        if preco_antigo != novo_preco:
            log = HistoricoPrecoCor(
                cor_id=produto.id,
                preco_anterior=preco_antigo,
                preco_novo=novo_preco,
                usuario_id=current_user.id
            )
            db.session.add(log)

        db.session.commit()
        flash('Atualizado com sucesso!', 'success')
    else:
        flash('Erro na atualização.', 'error')
        
    return redirect(url_for('produtos.gerenciar'))

@bp_produtos.route('/status/<int:id>', methods=['GET'])
@login_required
def alternar_status(id):
    produto = CorServico.query.get_or_404(id)
    produto.ativo = not produto.ativo
    db.session.commit()
    flash('Status alterado.', 'info')
    return redirect(url_for('produtos.gerenciar'))