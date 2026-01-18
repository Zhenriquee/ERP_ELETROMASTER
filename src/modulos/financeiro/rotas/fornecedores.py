from flask import render_template, redirect, url_for, flash
from flask_login import login_required

from src.extensoes import banco_de_dados as db
from src.modulos.financeiro.modelos import Fornecedor
from src.modulos.financeiro.formularios import FormularioFornecedor
from . import bp_financeiro

@bp_financeiro.route('/fornecedores', methods=['GET', 'POST'])
@login_required
def fornecedores():
    form = FormularioFornecedor()
    
    if form.validate_on_submit():
        novo_fornecedor = Fornecedor(
            nome_fantasia=form.nome_fantasia.data,
            razao_social=form.razao_social.data,
            cnpj=form.cnpj.data,
            telefone=form.telefone.data,
            email=form.email.data,
            cidade=form.cidade.data,
            estado=form.estado.data
        )
        db.session.add(novo_fornecedor)
        db.session.commit()
        flash(f'Fornecedor "{form.nome_fantasia.data}" cadastrado!', 'success')
        return redirect(url_for('financeiro.fornecedores'))
        
    lista_fornecedores = Fornecedor.query.filter_by(ativo=True).order_by(Fornecedor.nome_fantasia).all()
    
    return render_template('financeiro/fornecedores.html', form=form, fornecedores=lista_fornecedores)