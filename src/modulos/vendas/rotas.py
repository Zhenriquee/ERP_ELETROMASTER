from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import Venda, CorServico, HistoricoPrecoCor
from src.modulos.vendas.formularios import FormularioVendaWizard, FormularioCor
from decimal import Decimal

bp_vendas = Blueprint('vendas', __name__, url_prefix='/vendas')

# --- WIZARD DE VENDAS ---
@bp_vendas.route('/nova', methods=['GET', 'POST'])
@login_required
def nova_venda():
    form = FormularioVendaWizard()
    form.cor_id.choices = [(c.id, f"{c.nome} (R$ {c.preco_unitario}/{c.unidade_medida})") 
                           for c in CorServico.query.filter_by(ativo=True).all()]

    if request.method == 'POST':
        cor = CorServico.query.get(form.cor_id.data)
        
        # Lógica para definir quem é quem baseado no tipo
        if form.tipo_cliente.data == 'PF':
            nome_final = form.pf_nome.data
            doc_final = form.pf_cpf.data
            solicitante_final = None # PF não tem solicitante separado
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
            status='orcamento'
        )

        valor_bruto = nova.metragem_total * nova.quantidade_pecas * cor.preco_unitario
        nova.valor_base = valor_bruto
        
        # 1. Aplica Acréscimo (Novo)
        acrescimo = Decimal(form.input_acrescimo.data or 0)
        nova.valor_acrescimo = acrescimo
        
        valor_com_acrescimo = valor_bruto + acrescimo

        # 2. Aplica Desconto (Sobre o valor já com acréscimo ou base? Geralmente sobre a base + acréscimo)
        desc_input = Decimal(form.input_desconto.data or 0)
        desconto_reais = Decimal(0)
        
        if form.tipo_desconto.data == 'perc':
            desconto_reais = valor_com_acrescimo * (desc_input / 100)
        elif form.tipo_desconto.data == 'real':
            desconto_reais = desc_input
            
        nova.tipo_desconto = form.tipo_desconto.data
        nova.valor_desconto_aplicado = desconto_reais
        
        # 3. Final
        nova.valor_final = valor_com_acrescimo - desconto_reais

        db.session.add(nova)
        db.session.commit()
        flash(f'Venda #{nova.id} registrada com sucesso!', 'success')
        return redirect(url_for('dashboard'))

    cores_json = [{
        'id': c.id, 
        'preco': float(c.preco_unitario), 
        'unidade': c.unidade_medida
    } for c in CorServico.query.filter_by(ativo=True).all()]

    return render_template('vendas/nova_venda.html', form=form, cores_json=cores_json)

# --- ADMINISTRAÇÃO DE CORES ---
@bp_vendas.route('/admin/cores', methods=['GET', 'POST'])
@login_required
def admin_cores():
    # Validar permissão de gerente/dono aqui se necessário
    form = FormularioCor()
    cores = CorServico.query.all()

    if form.validate_on_submit():
        nova_cor = CorServico(
            nome=form.nome.data,
            unidade_medida=form.unidade.data,
            preco_unitario=form.preco.data
        )
        db.session.add(nova_cor)
        
        # Log de Histórico (Governança)
        # Como é criação, preço anterior é 0
        log = HistoricoPrecoCor(
            cor=nova_cor,
            preco_anterior=0,
            preco_novo=form.preco.data,
            usuario_id=current_user.id
        )
        db.session.add(log)
        db.session.commit()
        flash('Cor adicionada com sucesso!', 'success')
        return redirect(url_for('vendas.admin_cores'))

    return render_template('vendas/admin_cores.html', form=form, cores=cores)