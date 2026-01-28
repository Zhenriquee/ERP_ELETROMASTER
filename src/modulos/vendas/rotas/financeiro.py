from flask import redirect, url_for, flash, request
from flask_login import login_required, current_user
from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import Venda, Pagamento
from src.modulos.vendas.formularios import FormularioPagamento
from decimal import Decimal
from datetime import datetime
from src.modulos.autenticacao.permissoes import cargo_exigido  # <--- IMPORTAR

from . import bp_vendas

@bp_vendas.route('/servicos/<int:id>/pagamento', methods=['POST'])
@login_required
@cargo_exigido('vendas_operar')  # <--- PROTEÇÃO APLICADA
def registrar_pagamento(id):
    venda = Venda.query.get_or_404(id)
    form = FormularioPagamento()
    
    # Recebe valor do form ou calcula se for 'total'
    valor_pagamento = Decimal(0)
    tipo = request.form.get('tipo_recebimento')
    
    if tipo == 'total':
        valor_pagamento = venda.valor_restante
    else:
        try:
            valor_pagamento = Decimal(request.form.get('valor').replace(',', '.'))
        except:
            flash('Valor inválido.', 'error')
            # CORREÇÃO AQUI: Mudado de 'vendas.gestao_servicos' para 'vendas.listar_vendas'
            return redirect(url_for('vendas.listar_vendas'))

    if valor_pagamento <= 0:
        flash('O valor do pagamento deve ser maior que zero.', 'error')
        # CORREÇÃO AQUI
        return redirect(url_for('vendas.listar_vendas'))

    if valor_pagamento > venda.valor_restante:
        flash(f'Erro: O valor informado (R$ {valor_pagamento}) é maior que o restante (R$ {venda.valor_restante}).', 'error')
        # CORREÇÃO AQUI
        return redirect(url_for('vendas.listar_vendas'))

    # Registra o Pagamento
    novo_pgto = Pagamento(
        venda_id=venda.id,
        valor=valor_pagamento,
        data_pagamento=datetime.strptime(request.form.get('data_pagamento'), '%Y-%m-%d'),
        tipo=tipo,
        usuario_id=current_user.id
    )
    db.session.add(novo_pgto)
    
    # Atualiza status financeiro da venda
    db.session.commit() 
    
    if venda.valor_restante <= 0.01: # Margem de erro float
        venda.status_pagamento = 'pago'
    else:
        venda.status_pagamento = 'parcial'
        
    db.session.commit()
    
    flash('Pagamento registrado com sucesso!', 'success')
    # CORREÇÃO AQUI: O redirecionamento final também precisava ser corrigido
    return redirect(url_for('vendas.listar_vendas'))