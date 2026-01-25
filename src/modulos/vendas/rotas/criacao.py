from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import Venda, CorServico, hora_brasilia, ItemVenda, ItemVendaHistorico
from src.modulos.vendas.formularios import FormularioVendaWizard
from decimal import Decimal

# Importa o blueprint criado no __init__.py
from . import bp_vendas


# Função auxiliar para converter "1.234,56" em Decimal(1234.56)
def converter_decimal(valor_str):
    if not valor_str:
        return Decimal('0.00')
    if isinstance(valor_str, (float, int, Decimal)):
        return Decimal(valor_str)
    
    # Remove pontos de milhar e troca vírgula por ponto
    limpo = str(valor_str).replace('.', '').replace(',', '.')
    try:
        return Decimal(limpo)
    except:
        return Decimal('0.00')

@bp_vendas.route('/nova', methods=['GET', 'POST'])
@login_required
def nova_venda():
    form = FormularioVendaWizard()
    
    # 1. Popula o select com as cores ativas
    cores_ativas = CorServico.query.filter_by(ativo=True).order_by(CorServico.nome).all()
    form.cor_id.choices = [(c.id, c.nome) for c in cores_ativas]

    # 2. Lógica do POST (Salvar)
    if form.validate_on_submit():
        try:
            # --- Dados do Cliente ---
            if form.tipo_cliente.data == 'PJ':
                c_nome = form.pj_fantasia.data
                c_doc = form.pj_cnpj.data
                c_solicitante = form.pj_solicitante.data
            else:
                c_nome = form.pf_nome.data
                c_doc = form.pf_cpf.data
                c_solicitante = None

            # --- Preço ---
            cor_selecionada = CorServico.query.get(form.cor_id.data)
            
            preco_snapshot = 0.0
            if form.tipo_medida.data == 'm3':
                preco_snapshot = cor_selecionada.preco_m3 if cor_selecionada.preco_m3 else 0.0
            else:
                preco_snapshot = cor_selecionada.preco_m2 if cor_selecionada.preco_m2 else 0.0

            # --- CORREÇÃO: Conversão dos Valores Monetários/Numéricos ---
            # O form traz strings com vírgula (ex: "45,000") que quebram o banco
            metragem_limpa = converter_decimal(form.metragem_total.data)
            base_limpa = converter_decimal(form.valor_base.data)
            final_limpa = converter_decimal(form.valor_final.data)
            acrescimo_limpo = converter_decimal(form.valor_acrescimo.data)
            desconto_limpo = converter_decimal(form.valor_desconto_aplicado.data)

            # --- Criação da Venda ---
            nova_venda = Venda(
                tipo_cliente=form.tipo_cliente.data,
                cliente_nome=c_nome,
                cliente_documento=c_doc,
                cliente_solicitante=c_solicitante,
                cliente_contato=form.telefone.data,
                cliente_email=form.email.data,
                cliente_endereco=form.endereco.data,
                
                cor_id=cor_selecionada.id,
                cor_nome_snapshot=cor_selecionada.nome,
                preco_unitario_snapshot=preco_snapshot,
                
                tipo_medida=form.tipo_medida.data,
                dimensao_1=form.dimensao_1.data, # Esses campos o WTForms já converteu pois são DecimalField
                dimensao_2=form.dimensao_2.data,
                dimensao_3=form.dimensao_3.data,
                
                metragem_total=metragem_limpa, # Usando valor limpo
                quantidade_pecas=form.quantidade_pecas.data,
                
                valor_base=base_limpa,         # Usando valor limpo
                valor_acrescimo=acrescimo_limpo,
                tipo_desconto=form.tipo_desconto.data,
                valor_desconto_aplicado=desconto_limpo,
                valor_final=final_limpa,       # Usando valor limpo
                
                descricao_servico=form.descricao_servico.data,
                observacoes_internas=form.observacoes_internas.data,
                
                vendedor_id=current_user.id,
                status='orcamento'
            )
            
            db.session.add(nova_venda)
            db.session.commit()

            # --- Cria ItemVenda ---
            # Item também precisa receber os valores limpos se usasse esses campos, 
            # mas valor_total vem da venda que já está limpo no objeto Python (Decimal)
            novo_item = ItemVenda(
                venda_id=nova_venda.id,
                descricao=f"{cor_selecionada.nome} ({form.tipo_medida.data})",
                cor_id=cor_selecionada.id,
                quantidade=form.quantidade_pecas.data,
                valor_unitario=preco_snapshot,
                valor_total=nova_venda.valor_final,
                status='pendente'
            )
            db.session.add(novo_item)
            db.session.commit()

            # --- Histórico ---
            hist = ItemVendaHistorico(
                item_id=novo_item.id,
                usuario_id=current_user.id,
                status_anterior='-',
                status_novo='pendente',
                acao='Criado na venda'
            )
            db.session.add(hist)
            db.session.commit()

            flash('Venda registrada com sucesso!', 'success')
            return redirect(url_for('vendas.listar_vendas'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar venda: {str(e)}', 'error')
            print(f"Erro Nova Venda: {e}")

    # 3. Lógica do GET
    cores_json = [{
        'id': c.id, 
        'nome': c.nome,
        'preco_m2': float(c.preco_m2) if c.preco_m2 else 0.0,
        'preco_m3': float(c.preco_m3) if c.preco_m3 else 0.0
    } for c in cores_ativas]

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