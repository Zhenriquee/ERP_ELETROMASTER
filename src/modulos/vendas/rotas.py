from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import Venda, CorServico, Pagamento, hora_brasilia
from src.modulos.vendas.formularios import FormularioVendaWizard, FormularioPagamento
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import func

bp_vendas = Blueprint('vendas', __name__, url_prefix='/vendas')

# --- ROTAS DE CRIAÇÃO (MANTIDAS) ---
@bp_vendas.route('/nova', methods=['GET', 'POST'])
@login_required
def nova_venda():
    form = FormularioVendaWizard()
    form.cor_id.choices = [(c.id, f"{c.nome} (R$ {c.preco_unitario}/{c.unidade_medida})") 
                           for c in CorServico.query.filter_by(ativo=True).all()]

    if request.method == 'POST':
        cor = CorServico.query.get(form.cor_id.data)
        
        if form.tipo_cliente.data == 'PF':
            nome_final = form.pf_nome.data
            doc_final = form.pf_cpf.data
            solicitante_final = None
        else:
            nome_final = form.pj_fantasia.data
            doc_final = form.pj_cnpj.data
            solicitante_final = form.pj_solicitante.data

        nova = Venda(
            tipo_cliente=form.tipo_cliente.data,
            cliente_nome=nome_final,
            cliente_solicitante=solicitante_final,
            cliente_documento=doc_final,
            cliente_contato=form.telefone.data,
            cliente_email=form.email.data,
            cliente_endereco=form.endereco.data,
            descricao_servico=form.descricao_servico.data,
            observacoes_internas=form.observacoes_internas.data,
            tipo_medida=form.tipo_medida.data,
            dimensao_1=form.dim_1.data or 0,
            dimensao_2=form.dim_2.data or 0,
            dimensao_3=form.dim_3.data or 0,
            metragem_total=Decimal(form.metragem_calculada.data or 0),
            quantidade_pecas=form.qtd_pecas.data,
            cor_id=cor.id,
            cor_nome_snapshot=cor.nome,
            preco_unitario_snapshot=cor.preco_unitario,
            vendedor_id=current_user.id,
            # Se criado agora, entra como Pendente (Venda Confirmada)
            status='pendente' 
        )

        valor_bruto = nova.metragem_total * nova.quantidade_pecas * cor.preco_unitario
        nova.valor_base = valor_bruto
        
        acrescimo = Decimal(form.input_acrescimo.data or 0)
        nova.valor_acrescimo = acrescimo
        valor_com_acrescimo = valor_bruto + acrescimo

        desc_input = Decimal(form.input_desconto.data or 0)
        desconto_reais = Decimal(0)
        
        if form.tipo_desconto.data == 'perc':
            desconto_reais = valor_com_acrescimo * (desc_input / 100)
        elif form.tipo_desconto.data == 'real':
            desconto_reais = desc_input
            
        nova.tipo_desconto = form.tipo_desconto.data
        nova.valor_desconto_aplicado = desconto_reais
        nova.valor_final = valor_com_acrescimo - desconto_reais

        db.session.add(nova)
        db.session.commit()
        flash(f'Venda #{nova.id} registrada e enviada para produção!', 'success')
        return redirect(url_for('vendas.gestao_servicos'))

    cores_json = [{
        'id': c.id, 
        'preco': float(c.preco_unitario), 
        'unidade': c.unidade_medida
    } for c in CorServico.query.filter_by(ativo=True).all()]

    return render_template('vendas/nova_venda.html', form=form, cores_json=cores_json)

# --- GESTÃO DE SERVIÇOS (NOVA TELA) ---
@bp_vendas.route('/servicos', methods=['GET'])
@login_required
def gestao_servicos():
    # Recupera vendas que não são orçamento
    servicos = Venda.query.filter(Venda.status != 'orcamento').order_by(Venda.criado_em.desc()).all()
    
    # --- CÁLCULO DE KPIS ---
    hoje = hora_brasilia().date()
    inicio_mes = hoje.replace(day=1)
    data_30_dias_atras = hora_brasilia() - timedelta(days=30)
    
    # Financeiro
    total_vendido = db.session.query(func.sum(Venda.valor_final)).filter(Venda.status != 'orcamento', Venda.status != 'cancelado').scalar() or 0
    total_recebido_geral = db.session.query(func.sum(Pagamento.valor)).scalar() or 0
    a_receber = total_vendido - total_recebido_geral
    if a_receber < 0: a_receber = 0
    
    recebido_mes = db.session.query(func.sum(Pagamento.valor)).filter(Pagamento.data_pagamento >= inicio_mes).scalar() or 0
    
    # Operacional
    qtd_pendente = Venda.query.filter_by(status='pendente').count()
    qtd_producao = Venda.query.filter_by(status='producao').count()
    qtd_pronto = Venda.query.filter_by(status='pronto').count()
    
    # Novo KPI: Cancelados (Últimos 30 dias)
    qtd_cancelados_30d = Venda.query.filter(
        Venda.status == 'cancelado',
        Venda.data_cancelamento >= data_30_dias_atras
    ).count()

    form_pgto = FormularioPagamento()
    
    # Passamos lista de vendedores para o filtro no HTML
    vendedores = set(s.vendedor.nome for s in servicos)

    return render_template('vendas/gestao_servicos.html', 
                           servicos=servicos,
                           vendedores=vendedores,
                           kpi_receber=a_receber,
                           kpi_recebido_mes=recebido_mes,
                           qtd_pendente=qtd_pendente,
                           qtd_producao=qtd_producao,
                           qtd_pronto=qtd_pronto,
                           qtd_cancelados=qtd_cancelados_30d,
                           form_pgto=form_pgto)

# --- AÇÕES DE SERVIÇO ---
# ... (Mantenha os imports e rotas anteriores até chegar em mudar_status) ...

@bp_vendas.route('/servicos/<int:id>/status/<novo_status>')
@login_required
def mudar_status(id, novo_status):
    venda = Venda.query.get_or_404(id)
    mapa_status = {'producao': 'Em Produção', 'pronto': 'Pronto', 'entregue': 'Entregue'}
    
    if novo_status in mapa_status:
        venda.status = novo_status
        agora = hora_brasilia() # <--- Mudança aqui
        usuario_atual = current_user.id
        
        if novo_status == 'producao':
            venda.data_inicio_producao = agora
            venda.usuario_producao_id = usuario_atual
        elif novo_status == 'pronto':
            venda.data_pronto = agora
            venda.usuario_pronto_id = usuario_atual
        elif novo_status == 'entregue':
            venda.data_entrega = agora
            venda.usuario_entrega_id = usuario_atual

        db.session.commit()
        flash(f'Status atualizado para: {mapa_status[novo_status]}', 'success')
    
    return redirect(url_for('vendas.gestao_servicos'))

# --- NOVA ROTA: CANCELAR SERVIÇO ---
@bp_vendas.route('/servicos/<int:id>/cancelar', methods=['POST'])
@login_required
def cancelar_servico(id):
    venda = Venda.query.get_or_404(id)
    if venda.status == 'entregue' and venda.valor_restante <= 0.01:
        flash('Não é possível cancelar um serviço finalizado e totalmente pago.', 'error')
        return redirect(url_for('vendas.gestao_servicos'))
    motivo = request.form.get('motivo_cancelamento')
    
    if not motivo or len(motivo.strip()) < 5:
        flash('É obrigatório informar o motivo do cancelamento (mínimo 5 caracteres).', 'error')
        return redirect(url_for('vendas.gestao_servicos'))
    
    venda.status = 'cancelado'
    venda.motivo_cancelamento = motivo
    venda.data_cancelamento = hora_brasilia()
    venda.usuario_cancelamento_id = current_user.id
    
    db.session.commit()
    flash('Serviço cancelado com sucesso.', 'info')
    return redirect(url_for('vendas.gestao_servicos'))

# ... (Mantenha a rota registrar_pagamento igual, ela já usa current_user.id) ...

@bp_vendas.route('/servicos/<int:id>/pagamento', methods=['POST'])
@login_required
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
            return redirect(url_for('vendas.gestao_servicos'))

    if valor_pagamento <= 0:
        flash('O valor do pagamento deve ser maior que zero.', 'error')
        return redirect(url_for('vendas.gestao_servicos'))

    if valor_pagamento > venda.valor_restante:
        flash(f'Erro: O valor informado (R$ {valor_pagamento}) é maior que o restante (R$ {venda.valor_restante}).', 'error')
        return redirect(url_for('vendas.gestao_servicos'))

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
    # Precisamos commitar o pagamento antes para calcular o novo total pago
    db.session.commit() 
    
    if venda.valor_restante <= 0.01: # Margem de erro float
        venda.status_pagamento = 'pago'
    else:
        venda.status_pagamento = 'parcial'
        
    db.session.commit()
    
    flash('Pagamento registrado com sucesso!', 'success')
    return redirect(url_for('vendas.gestao_servicos'))