from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import CorServico, HistoricoPrecoCor
from src.modulos.produtos.formularios import FormularioProduto

bp_produtos = Blueprint('produtos', __name__, url_prefix='/produtos')

@bp_produtos.route('/', methods=['GET', 'POST'])
@login_required
def gerenciar():
    form = FormularioProduto()
    
    if form.validate_on_submit():
        # Validação simples: pelo menos um preço deve existir
        pm2 = form.preco_m2.data
        pm3 = form.preco_m3.data
        
        if not pm2 and not pm3:
            flash('Informe pelo menos um preço (m² ou m³).', 'error')
        else:
            nova_cor = CorServico(
                nome=form.nome.data,
                preco_m2=pm2,
                preco_m3=pm3,
                ativo=True
            )
            db.session.add(nova_cor)
            db.session.commit()
            
            # Log Inicial
            log = HistoricoPrecoCor(
                cor_id=nova_cor.id,
                preco_m2_anterior=0, preco_m2_novo=pm2,
                preco_m3_anterior=0, preco_m3_novo=pm3,
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
        antigo_m2 = produto.preco_m2
        antigo_m3 = produto.preco_m3
        
        novo_m2 = form.preco_m2.data
        novo_m3 = form.preco_m3.data

        if not novo_m2 and not novo_m3:
             flash('O produto precisa ter ao menos um preço.', 'error')
             return redirect(url_for('produtos.gerenciar'))

        produto.nome = form.nome.data
        produto.preco_m2 = novo_m2
        produto.preco_m3 = novo_m3

        # Registra histórico se houve mudança
        if antigo_m2 != novo_m2 or antigo_m3 != novo_m3:
            log = HistoricoPrecoCor(
                cor_id=produto.id,
                preco_m2_anterior=antigo_m2, preco_m2_novo=novo_m2,
                preco_m3_anterior=antigo_m3, preco_m3_novo=novo_m3,
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