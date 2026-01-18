from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import Venda, CorServico, hora_brasilia, ItemVenda
from src.modulos.vendas.formularios import FormularioVendaWizard
from decimal import Decimal

# Importa o blueprint criado no __init__.py
from . import bp_vendas


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
            status='pendente', # Já entra como pendente pois foi "fechada" na tela
            criado_em=hora_brasilia()  # <--- FORÇAR AQUI
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