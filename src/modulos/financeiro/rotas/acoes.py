from flask import redirect, url_for, flash
from flask_login import login_required
from datetime import date

from src.extensoes import banco_de_dados as db
from src.modulos.financeiro.modelos import Despesa
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
    db.session.delete(despesa)
    db.session.commit()
    flash('Lançamento excluído.', 'info')
    return redirect(url_for('financeiro.painel'))