from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import Venda, CorServico, Pagamento, hora_brasilia, ItemVenda
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

# --- ROTA PARA ABRIR A NOVA TELA ---
@bp_vendas.route('/nova-multipla', methods=['GET'])
@login_required
def nova_venda_multipla():
    # Envia as cores como JSON para o JavaScript usar no Grid
    cores_json = [{
        'id': c.id, 
        'nome': c.nome,
        'unidade': c.unidade_medida
    } for c in CorServico.query.filter_by(ativo=True).all()]
    
    return render_template('vendas/nova_venda_multipla.html', cores_json=cores_json)

# --- ROTA PARA SALVAR A VENDA MÚLTIPLA ---
@bp_vendas.route('/salvar-multipla', methods=['POST'])
@login_required
def salvar_venda_multipla():
    try:
        # 1. Dados do Cliente (Header)
        tipo_cliente = request.form.get('tipo_cliente')
        
        if tipo_cliente == 'PF':
            nome = request.form.get('pf_nome')
            doc = request.form.get('pf_cpf')
            solicitante = None
        else:
            nome = request.form.get('pj_fantasia')
            doc = request.form.get('pj_cnpj')
            solicitante = request.form.get('pj_solicitante')

        # 2. Cria a Venda (Cabeçalho)
        nova_venda = Venda(
            modo='multipla', # Identifica que é o novo método
            tipo_cliente=tipo_cliente,
            cliente_nome=nome,
            cliente_documento=doc,
            cliente_solicitante=solicitante,
            cliente_contato=request.form.get('telefone'),
            cliente_email=request.form.get('email'),
            cliente_endereco=request.form.get('endereco'),
            observacoes_internas=request.form.get('obs_internas'),
            descricao_servico="Serviço com Múltiplos Itens (Ver Detalhes)", # Texto padrão
            vendedor_id=current_user.id,
            status='pendente' # Já entra como pendente pois foi "fechada" na tela
        )

        # 3. Processa os Itens do Grid
        # O form envia names como "itens[0][descricao]", "itens[1][descricao]"
        # Vamos iterar os índices
        itens_para_adicionar = []
        valor_base_total = Decimal(0)
        
        # Como o request.form é um dicionário flat, precisamos achar os índices
        # Uma forma simples é iterar chaves ou assumir um limite. 
        # Melhor: iterar e buscar os padrões.
        
        # Estratégia robusta: Agrupar dados
        dados_itens = {}
        for key, value in request.form.items():
            if key.startswith('itens['):
                # Extrai índice e campo. Ex: itens[0][descricao] -> idx=0, field=descricao
                parts = key.replace(']', '').split('[')
                idx = int(parts[1])
                field = parts[2]
                
                if idx not in dados_itens: dados_itens[idx] = {}
                dados_itens[idx][field] = value

        # Cria os objetos ItemVenda
        for idx, item_data in dados_itens.items():
            qtd = int(item_data['qtd'])
            unit = Decimal(item_data['unit'])
            total = Decimal(item_data['total'])
            
            valor_base_total += total
            
            novo_item = ItemVenda(
                descricao=item_data['descricao'],
                cor_id=int(item_data['cor_id']),
                quantidade=qtd,
                valor_unitario=unit,
                valor_total=total
            )
            itens_para_adicionar.append(novo_item)

        # 4. Financeiro Global
        nova_venda.valor_base = valor_base_total
        nova_venda.valor_acrescimo = Decimal(request.form.get('acrescimo') or 0)
        
        tipo_desc = request.form.get('tipo_desconto')
        val_desc_input = Decimal(request.form.get('valor_desconto') or 0)
        
        valor_com_acrescimo = nova_venda.valor_base + nova_venda.valor_acrescimo
        valor_desconto = Decimal(0)
        
        if tipo_desc == 'perc':
            valor_desconto = valor_com_acrescimo * (val_desc_input / 100)
        else:
            valor_desconto = val_desc_input
            
        nova_venda.valor_desconto_aplicado = valor_desconto
        nova_venda.valor_final = valor_com_acrescimo - valor_desconto
        
        # Campos obrigatórios do legado (preenche com dummy para não quebrar constraint NOT NULL)
        # Se você fez migration alterando para Nullable, isso não é necessário, mas é bom prevenir
        nova_venda.tipo_medida = 'un'
        nova_venda.dimensao_1 = 0
        nova_venda.dimensao_2 = 0
        nova_venda.metragem_total = 0
        nova_venda.cor_id = itens_para_adicionar[0].cor_id if itens_para_adicionar else 1 # Pega a cor do primeiro ou padrão

        # 5. Salva tudo
        db.session.add(nova_venda)
        db.session.flush() # Gera o ID da venda
        
        for item in itens_para_adicionar:
            item.venda_id = nova_venda.id
            db.session.add(item)
            
        db.session.commit()
        flash(f'Venda Múltipla #{nova_venda.id} criada com sucesso!', 'success')
        return redirect(url_for('vendas.gestao_servicos'))

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar venda: {str(e)}', 'error')
        return redirect(url_for('vendas.nova_venda_multipla'))
    
@bp_vendas.route('/itens/<int:id>/status/<novo_status>')
@login_required
def mudar_status_item(id, novo_status):
    item = ItemVenda.query.get_or_404(id)
    venda_pai = Venda.query.get(item.venda_id)
    
    mapa_status = {
        'pendente': 'Pendente',
        'producao': 'Em Produção',
        'pronto': 'Pronto',
        'entregue': 'Entregue'
    }
    
    if novo_status in mapa_status:
        item.status = novo_status
        agora = hora_brasilia() # Garante data/hora correta (Brasília)
        
        # Atualiza data específica do item
        if novo_status == 'producao':
            item.data_inicio_producao = agora
            # Opcional: Se um item entrou em produção, a Venda pai também entra
            if venda_pai.status == 'pendente':
                venda_pai.status = 'producao'
                venda_pai.data_inicio_producao = agora
                venda_pai.usuario_producao_id = current_user.id
                
        elif novo_status == 'pronto':
            item.data_pronto = agora
            
        elif novo_status == 'entregue':
            item.data_entregue = agora

        db.session.commit()
        flash(f'Item "{item.descricao}" atualizado para: {mapa_status[novo_status]}', 'success')
    
    return redirect(url_for('vendas.gestao_servicos'))    