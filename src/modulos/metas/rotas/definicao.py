# src/modulos/metas/rotas/definicao.py

from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
import calendar

from src.extensoes import banco_de_dados as db
from src.modulos.metas.modelos import MetaMensal, MetaVendedor
from src.modulos.metas.formularios import FormularioMetaLoja
from src.modulos.autenticacao.modelos import Usuario
from . import bp_metas

# Função Auxiliar: Calcula dias úteis baseado na config
def calcular_dias_uteis(ano, mes, dias_semana_str, feriados_str):
    # Converte '0,1,2' para lista de inteiros
    dias_trabalho = [int(d) for d in dias_semana_str.split(',') if d]
    
    # Converte '1, 15' para lista de inteiros
    feriados = []
    if feriados_str:
        try:
            feriados = [int(d.strip()) for d in feriados_str.replace('.',',').split(',') if d.strip().isdigit()]
        except:
            pass
            
    cal = calendar.monthcalendar(ano, mes)
    count = 0
    
    for semana in cal:
        for dia_idx, dia_mes in enumerate(semana):
            # dia_mes é 0 se for padding do calendário (dias de outro mês)
            if dia_mes != 0:
                # Verifica se o dia da semana está marcado E se não é feriado
                if dia_idx in dias_trabalho and dia_mes not in feriados:
                    count += 1
    return count

@bp_metas.route('/nova', methods=['GET', 'POST'])
@login_required
def nova_meta():
    form = FormularioMetaLoja()
    
    if form.validate_on_submit():
        # Prepara strings para salvar no banco
        str_semana = ",".join(form.dias_semana.data)
        str_feriados = form.feriados.data.strip() if form.feriados.data else ""
        
        # Calcula dias úteis automaticamente
        qtd_dias_uteis = calcular_dias_uteis(form.ano.data, form.mes.data, str_semana, str_feriados)
        
        if qtd_dias_uteis == 0:
            flash('Erro: A configuração resultou em 0 dias úteis.', 'error')
            return render_template('metas/nova_meta.html', form=form)

        # Verifica existência (Lógica Mantida)
        existente = MetaMensal.query.filter_by(mes=form.mes.data, ano=form.ano.data).first()
        if existente:
            flash(f'Já existe meta para {form.mes.data}/{form.ano.data}. Redirecionando para edição.', 'warning')
            return redirect(url_for('metas.editar_meta', id=existente.id))
            
        nova = MetaMensal(
            mes=form.mes.data,
            ano=form.ano.data,
            valor_loja=form.valor_loja.data,
            dias_uteis=qtd_dias_uteis, # Automático
            config_semana=str_semana,
            config_feriados=str_feriados,
            criado_por_id=current_user.id
        )
        db.session.add(nova)
        db.session.commit()
        
        flash(f'Meta definida! Serão {qtd_dias_uteis} dias de trabalho.', 'success')
        return redirect(url_for('metas.distribuir_meta', id=nova.id))
        
    return render_template('metas/nova_meta.html', form=form)

# NOVA ROTA: EDITAR META
@bp_metas.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_meta(id):
    meta = MetaMensal.query.get_or_404(id)
    form = FormularioMetaLoja(obj=meta)
    
    if request.method == 'GET':
        # Popula o multicheckbox a partir da string do banco "0,1,2"
        if meta.config_semana:
            form.dias_semana.data = meta.config_semana.split(',')
        if meta.config_feriados:
            form.feriados.data = meta.config_feriados

    if form.validate_on_submit():
        str_semana = ",".join(form.dias_semana.data)
        str_feriados = form.feriados.data.strip() if form.feriados.data else ""
        qtd_dias_uteis = calcular_dias_uteis(form.ano.data, form.mes.data, str_semana, str_feriados)
        
        meta.mes = form.mes.data
        meta.ano = form.ano.data
        meta.valor_loja = form.valor_loja.data
        meta.config_semana = str_semana
        meta.config_feriados = str_feriados
        meta.dias_uteis = qtd_dias_uteis
        
        db.session.commit()
        flash('Configurações da meta atualizadas!', 'success')
        return redirect(url_for('metas.distribuir_meta', id=meta.id))

    return render_template('metas/nova_meta.html', form=form, editando=True)

@bp_metas.route('/distribuir/<int:id>', methods=['GET', 'POST'])
@login_required
def distribuir_meta(id):
    meta_mensal = MetaMensal.query.get_or_404(id)
    
    # --- CORREÇÃO: FILTRAR POR EQUIPE ---
    # Busca apenas usuários ativos QUE PERTENCEM À EQUIPE DE VENDAS
    # Usamos o ilike para ignorar maiúsculas/minúsculas
    vendedores = Usuario.query.filter(
        Usuario.ativo == True,
        Usuario.equipe.ilike('vendas')
    ).all()
    
    # Opção 2 (Se quiser filtrar): Verifique como está escrito no seu banco.
    # Exemplo: Se cadastrou "Vendedor" (Maiúsculo), o filtro 'vendedor' falha.
    # vendedores = Usuario.query.filter(Usuario.cargo.in_(['Vendedor', 'Supervisor', 'vendedor', 'supervisor', 'admin'])).all()
    
    if not vendedores:
        flash('Atenção: Nenhum usuário ativo encontrado para distribuir a meta.', 'warning')
    
    if request.method == 'POST':
        total_distribuido = 0
        
        # Limpa metas anteriores desse mês
        MetaVendedor.query.filter_by(meta_mensal_id=id).delete()
        
        for vend in vendedores:
            # O nome do input no HTML é 'meta_ID'
            valor_input = request.form.get(f'meta_{vend.id}')
            
            if valor_input:
                # Tratamento para converter "1.000,00" ou "1000.00" para float
                try:
                    valor_limpo = valor_input.replace('.', '').replace(',', '.')
                    valor_decimal = float(valor_limpo)
                except ValueError:
                    valor_decimal = 0.0
                
                if valor_decimal > 0:
                    mv = MetaVendedor(
                        meta_mensal_id=id,
                        usuario_id=vend.id,
                        valor_meta=valor_decimal
                    )
                    db.session.add(mv)
                    total_distribuido += valor_decimal
        
        db.session.commit()
        
        diferenca = float(meta_mensal.valor_loja) - total_distribuido
        if abs(diferenca) > 1:
            flash(f'Metas salvas! Diferença de R$ {diferenca:.2f} em relação à meta da loja.', 'warning')
        else:
            flash('Metas distribuídas com sucesso!', 'success')
            
        return redirect(url_for('metas.painel'))
    
    # Sugestão de divisão igualitária
    sugestao_individual = float(meta_mensal.valor_loja) / len(vendedores) if vendedores else 0
    
    # Recupera valores já salvos
    metas_salvas = {m.usuario_id: m.valor_meta for m in meta_mensal.metas_vendedores}
    
    return render_template('metas/distribuir.html', 
                           meta=meta_mensal, 
                           vendedores=vendedores, 
                           sugestao=sugestao_individual,
                           metas_salvas=metas_salvas)