import os
from werkzeug.utils import secure_filename
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import Venda, CorServico, hora_brasilia, ItemVenda, ItemVendaHistorico, FotoItemVenda
from src.modulos.vendas.formularios import FormularioVendaWizard
from src.modulos.estoque.modelos import ProdutoEstoque
from decimal import Decimal
from src.modulos.autenticacao.permissoes import cargo_exigido
from . import bp_vendas

# ... (Função converter_decimal mantida) ...
def converter_decimal(valor_str):
    if not valor_str: return Decimal('0.00')
    if isinstance(valor_str, (float, int, Decimal)): return Decimal(valor_str)
    limpo = str(valor_str).replace('.', '').replace(',', '.')
    try: return Decimal(limpo)
    except: return Decimal('0.00')

def salvar_fotos_item(item_id, arquivos):
    """Função auxiliar para salvar fotos"""
    if not arquivos: return
    
    # Cria pasta se não existir
    upload_folder = os.path.join('src', 'static', 'uploads', 'vendas')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
        
    contador = 0
    for arquivo in arquivos:
        if arquivo and arquivo.filename and contador < 3: # Limite de 3
            filename = secure_filename(f"item_{item_id}_{hora_brasilia().strftime('%Y%m%d%H%M%S')}_{contador}.jpg")
            caminho_completo = os.path.join(upload_folder, filename)
            arquivo.save(caminho_completo)
            
            # Salva no banco (caminho relativo para o HTML)
            caminho_relativo = f"uploads/vendas/{filename}"
            foto = FotoItemVenda(
                item_venda_id=item_id,
                caminho_arquivo=caminho_relativo,
                etapa='recebimento', # Etapa inicial
                enviado_por_id=current_user.id
            )
            db.session.add(foto)
            contador += 1

@bp_vendas.route('/nova', methods=['GET', 'POST'])
@login_required
@cargo_exigido('vendas_operar')
def nova_venda():
    form = FormularioVendaWizard()
    produtos_ativos = ProdutoEstoque.query.filter_by(ativo=True).order_by(ProdutoEstoque.nome).all()
    form.produto_id.choices = [(p.id, p.nome) for p in produtos_ativos]

    if form.validate_on_submit():
        try:
            # ... (Lógica de Cliente igual ao anterior) ...
            if form.tipo_cliente.data == 'PJ':
                c_nome = form.pj_fantasia.data
                c_doc = form.pj_cnpj.data
                c_solicitante = form.pj_solicitante.data
            else:
                c_nome = form.pf_nome.data
                c_doc = form.pf_cpf.data
                c_solicitante = None

            produto_selecionado = ProdutoEstoque.query.get(form.produto_id.data)
            if form.tipo_medida.data == 'm3':
                preco_snapshot = produto_selecionado.preco_m3 or Decimal(0)
            else:
                preco_snapshot = produto_selecionado.preco_m2 or Decimal(0)

            nova_venda = Venda(
                prioridade=form.prioridade.data, # <--- NOVO CAMPO
                tipo_cliente=form.tipo_cliente.data,
                cliente_nome=c_nome,
                cliente_documento=c_doc,
                cliente_solicitante=c_solicitante,
                cliente_contato=form.telefone.data,
                cliente_email=form.email.data,
                cliente_endereco=form.endereco.data,
                produto_id=produto_selecionado.id,
                cor_nome_snapshot=produto_selecionado.nome,
                preco_unitario_snapshot=preco_snapshot,
                tipo_medida=form.tipo_medida.data,
                dimensao_1=form.dimensao_1.data, 
                dimensao_2=form.dimensao_2.data,
                dimensao_3=form.dimensao_3.data,
                metragem_total=converter_decimal(form.metragem_total.data), 
                quantidade_pecas=form.quantidade_pecas.data,
                valor_base=converter_decimal(form.valor_base.data),         
                valor_acrescimo=converter_decimal(form.valor_acrescimo.data),
                tipo_desconto=form.tipo_desconto.data,
                valor_desconto_aplicado=converter_decimal(form.valor_desconto_aplicado.data),
                valor_final=converter_decimal(form.valor_final.data),       
                descricao_servico=form.descricao_servico.data,
                observacoes_internas=form.observacoes_internas.data,
                vendedor_id=current_user.id,
                status='pendente',
                status_pagamento='pendente',
                criado_em=hora_brasilia()
            )
            
            db.session.add(nova_venda)
            db.session.flush()

            novo_item = ItemVenda(
                venda_id=nova_venda.id,
                descricao=f"{produto_selecionado.nome} ({form.tipo_medida.data})",
                produto_id=produto_selecionado.id,
                quantidade=form.quantidade_pecas.data,
                valor_unitario=preco_snapshot,
                valor_total=nova_venda.valor_final,
                status='pendente',
                
            )
            db.session.add(novo_item)
            db.session.flush() # Necessário para ter o ID do item para as fotos

            # --- SALVAR FOTOS (Venda Simples) ---
            arquivos = request.files.getlist('fotos_pecas')
            salvar_fotos_item(novo_item.id, arquivos)
            
            db.session.commit()
            flash('Venda registrada com sucesso!', 'success')
            return redirect(url_for('vendas.listar_vendas'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao registrar venda: {str(e)}', 'error')
            print(f"Erro Nova Venda: {e}")

    # ... (Restante igual: preparação do JSON) ...
    produtos_json = [{
        'id': p.id, 
        'nome': p.nome,
        'preco_m2': float(p.preco_m2) if p.preco_m2 else 0.0,
        'preco_m3': float(p.preco_m3) if p.preco_m3 else 0.0
    } for p in produtos_ativos]

    return render_template('vendas/nova_venda.html', form=form, produtos_json=produtos_json)

# ... (Rota nova_venda_multipla mantida igual) ...
@bp_vendas.route('/nova-multipla', methods=['GET'])
@login_required
@cargo_exigido('vendas_operar')
def nova_venda_multipla():
    produtos_ativos = ProdutoEstoque.query.filter_by(ativo=True).order_by(ProdutoEstoque.nome).all()
    produtos_json = [{
        'id': p.id, 
        'nome': p.nome,
        'unidade_padrao': p.unidade,
        'preco_m2': float(p.preco_m2) if p.preco_m2 else 0.0,
        'preco_m3': float(p.preco_m3) if p.preco_m3 else 0.0
    } for p in produtos_ativos]
    return render_template('vendas/nova_venda_multipla.html', produtos_json=produtos_json)

@bp_vendas.route('/salvar-multipla', methods=['POST'])
@login_required
@cargo_exigido('vendas_operar')
def salvar_venda_multipla():
    try:
        # ... (Logica Cliente igual) ...
        tipo_cliente = request.form.get('tipo_cliente')
        if tipo_cliente == 'PF':
            nome = request.form.get('pf_nome')
            doc = request.form.get('pf_cpf')
            solicitante = None
        else:
            nome = request.form.get('pj_fantasia')
            doc = request.form.get('pj_cnpj')
            solicitante = request.form.get('pj_solicitante')

        # Captura Prioridade (Checkbox no HTML retorna 'on' ou nada)
        is_prioridade = True if request.form.get('prioridade') == 'on' else False

        nova_venda = Venda(
            modo='multipla',
            prioridade=is_prioridade, # <--- NOVO
            tipo_cliente=tipo_cliente,
            cliente_nome=nome,
            cliente_documento=doc,
            cliente_solicitante=solicitante,
            cliente_contato=request.form.get('telefone'),
            cliente_email=request.form.get('email'),
            cliente_endereco=request.form.get('endereco'),
            observacoes_internas=request.form.get('obs_internas'),
            descricao_servico="Serviço com Múltiplos Itens", 
            vendedor_id=current_user.id,
            status='pendente', 
            status_pagamento='pendente',
            criado_em=hora_brasilia()
        )

        itens_para_adicionar = []
        valor_base_total = Decimal(0)
        
        # ... (Processamento de Itens igual) ...
        dados_itens = {}
        for key, value in request.form.items():
            if key.startswith('itens['):
                parts = key.replace(']', '').split('[')
                idx = int(parts[1])
                field = parts[2]
                if idx not in dados_itens: dados_itens[idx] = {}
                dados_itens[idx][field] = value

        primeiro_produto_id = None

        for idx, item_data in dados_itens.items():
            qtd = Decimal(item_data['qtd'])
            unit_price = Decimal(item_data['unit'])
            total = Decimal(item_data['total'])
            prod_id = int(item_data['produto_id'])
            
            if not primeiro_produto_id: primeiro_produto_id = prod_id
            valor_base_total += total
            
            novo_item = ItemVenda(
                descricao=item_data['descricao'],
                produto_id=prod_id, 
                quantidade=qtd,
                valor_unitario=unit_price,
                valor_total=total,
                status='pendente'
            )
            itens_para_adicionar.append(novo_item)

        # ... (Cálculo Financeiro igual) ...
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
        nova_venda.tipo_medida = 'un'
        nova_venda.dimensao_1 = 0
        nova_venda.dimensao_2 = 0
        nova_venda.metragem_total = 0
        nova_venda.produto_id = primeiro_produto_id 

        db.session.add(nova_venda)
        db.session.flush() 
        
        primeiro_item_salvo = None # Referência para salvar as fotos

        for i, item in enumerate(itens_para_adicionar):
            item.venda_id = nova_venda.id
            db.session.add(item)
            db.session.flush() 
            
            if i == 0: primeiro_item_salvo = item # Pega o primeiro item para vincular as fotos gerais

            # Log... (mantido)
            log = ItemVendaHistorico(
                item_id=item.id,
                usuario_id=current_user.id,
                status_anterior='-',
                status_novo='pendente',
                acao='Criado na venda múltipla',
                data_acao=hora_brasilia()
            )
            db.session.add(log)
            
        # --- SALVAR FOTOS (Venda Múltipla) ---
        # Vinculamos as fotos gerais ao PRIMEIRO item da lista, já que o modelo exige vínculo com Item
        if primeiro_item_salvo:
            arquivos = request.files.getlist('fotos_pecas')
            salvar_fotos_item(primeiro_item_salvo.id, arquivos)

        db.session.commit()
        flash(f'Venda Múltipla #{nova_venda.id} criada com sucesso!', 'success')
        return redirect(url_for('vendas.listar_vendas'))

    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao salvar venda: {str(e)}', 'error')
        print(f"Erro: {e}")
        return redirect(url_for('vendas.nova_venda_multipla'))