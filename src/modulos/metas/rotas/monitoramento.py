# src/modulos/metas/rotas/monitoramento.py

from flask import render_template, request, jsonify
from flask_login import login_required
from src.modulos.autenticacao.permissoes import cargo_exigido
from datetime import date
from sqlalchemy import func, extract
import calendar

from src.extensoes import banco_de_dados as db
from src.modulos.metas.modelos import MetaMensal, MetaVendedor
from src.modulos.vendas.modelos import Venda, Pagamento
from . import bp_metas

def fmt_moeda(valor):
    if valor is None:
        valor = 0.0
    return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@bp_metas.route('/', methods=['GET'])
@login_required
@cargo_exigido('metas_acesso')
def painel():
    hoje = date.today()
    
    try:
        mes_atual = int(request.args.get('mes', hoje.month))
        ano_atual = int(request.args.get('ano', hoje.year))
    except ValueError:
        mes_atual = hoje.month
        ano_atual = hoje.year

    meta_config = MetaMensal.query.filter_by(mes=mes_atual, ano=ano_atual).first()
    
    if not meta_config:
        return render_template('metas/sem_meta.html', mes_filtro=mes_atual, ano_filtro=ano_atual)

    # 1. DADOS GERAIS
    # Antes: Filtrava Venda.criado_em
    # Novo:
    total_recebido_loja = db.session.query(func.sum(Pagamento.valor))\
        .filter(
            extract('month', Pagamento.data_pagamento) == mes_atual,
            extract('year', Pagamento.data_pagamento) == ano_atual
        ).scalar() or 0
        
    perc_loja = (float(total_recebido_loja) / float(meta_config.valor_loja)) * 100
    
    # =======================================================
    # 2. CALENDÁRIO COM META DINÂMICA
    # =======================================================
    dias_trabalho = [int(d) for d in meta_config.config_semana.split(',')]
    feriados = []
    if meta_config.config_feriados:
        try:
            feriados = [int(d) for d in meta_config.config_feriados.replace('.',',').split(',') if d.strip().isdigit()]
        except:
            pass

    recebimentos_diarios = db.session.query(
        func.extract('day', Pagamento.data_pagamento).label('dia'),
        func.sum(Pagamento.valor).label('total')
    ).filter(
        func.extract('month', Pagamento.data_pagamento) == mes_atual,
        func.extract('year', Pagamento.data_pagamento) == ano_atual
    ).group_by('dia').all()

    mapa_vendas = {int(p.dia): float(p.total) for p in recebimentos_diarios}
    cal = calendar.monthcalendar(ano_atual, mes_atual)
    
    # Levanta o total de dias úteis no mês
    dias_uteis_lista = []
    for semana in cal:
        for dia_idx, dia_numero in enumerate(semana):
            if dia_numero != 0:
                if dia_numero not in feriados and dia_idx in dias_trabalho:
                    dias_uteis_lista.append(dia_numero)
                    
    meta_total_loja = float(meta_config.valor_loja)
    meta_diaria_hoje = meta_total_loja / len(dias_uteis_lista) if dias_uteis_lista else 0
    
    calendario_dados = []
    eh_mes_passado = (ano_atual < hoje.year) or (ano_atual == hoje.year and mes_atual < hoje.month)
    eh_mes_atual = (ano_atual == hoje.year and mes_atual == hoje.month)
    
    recebido_acumulado = 0
    
    for semana in cal:
        semana_dados = []
        for dia_idx, dia_numero in enumerate(semana):
            if dia_numero == 0:
                semana_dados.append({'tipo': 'vazio'})
                continue
                
            eh_feriado = dia_numero in feriados
            eh_trabalho = dia_idx in dias_trabalho
            
            if eh_mes_passado:
                eh_futuro = False
            elif eh_mes_atual:
                eh_futuro = dia_numero > hoje.day
            else:
                eh_futuro = True
            
            vendido_no_dia = mapa_vendas.get(dia_numero, 0)
            
            info = {
                'dia': dia_numero,
                'tipo': 'padrao',
                'vendido': vendido_no_dia,
                'meta_batida': False,
                'futuro': eh_futuro,
                'classe_cor_texto': 'text-gray-800'
            }
            
            if eh_feriado:
                info['tipo'] = 'feriado'
            elif not eh_trabalho:
                info['tipo'] = 'folga'
            else:
                info['tipo'] = 'trabalho'
                
                # ==========================================
                # VIAJANDO NO TEMPO: Meta Dinâmica DAQUELE DIA
                # ==========================================
                dias_restantes = len([d for d in dias_uteis_lista if d >= dia_numero])
                if dias_restantes > 0:
                    meta_do_dia = (meta_total_loja - recebido_acumulado) / dias_restantes
                else:
                    meta_do_dia = 0
                    
                if meta_do_dia < 0: meta_do_dia = 0
                
                # Salva a meta dinâmica do dia ATUAL para exibir no card superior grandão
                if eh_mes_atual and dia_numero == hoje.day:
                    meta_diaria_hoje = meta_do_dia
                
                if not info['futuro']:
                    meta_batida = vendido_no_dia >= meta_do_dia
                    info['meta_batida'] = meta_batida
                    info['classe_cor_texto'] = 'text-green-700' if meta_batida else 'text-red-700'
                
                # O que a equipe gerou hoje abate o rombo de amanhã
                recebido_acumulado += vendido_no_dia
            
            semana_dados.append(info)
        calendario_dados.append(semana_dados)

    # =======================================================
    # 3. RANKING DE VENDEDORES COM META DINÂMICA
    # =======================================================
    metas_vendedores = MetaVendedor.query.filter_by(meta_mensal_id=meta_config.id).all()
    ranking = []
    
    for mv in metas_vendedores:
        recebido_total = db.session.query(func.sum(Pagamento.valor))\
            .join(Venda, Pagamento.venda_id == Venda.id)\
            .filter(
                Venda.vendedor_id == mv.usuario_id,
                extract('month', Pagamento.data_pagamento) == mes_atual,
                extract('year', Pagamento.data_pagamento) == ano_atual
            ).scalar() or 0
            
        perc = (float(recebido_total) / float(mv.valor_meta)) * 100 if mv.valor_meta > 0 else 0
        
        # O vendedor também ganha uma meta dinâmica pessoal para correr atrás do prejuízo
        if eh_mes_atual:
            recebido_ate_ontem = db.session.query(func.sum(Pagamento.valor))\
                .join(Venda, Pagamento.venda_id == Venda.id)\
                .filter(
                    Venda.vendedor_id == mv.usuario_id,
                    extract('month', Pagamento.data_pagamento) == mes_atual,
                    extract('year', Pagamento.data_pagamento) == ano_atual,
                    func.date(Pagamento.data_pagamento) < hoje
                ).scalar() or 0
                
            dias_restantes_hoje = len([d for d in dias_uteis_lista if d >= hoje.day])
            if dias_restantes_hoje > 0:
                m_diaria = (float(mv.valor_meta) - float(recebido_ate_ontem)) / dias_restantes_hoje
            else:
                m_diaria = 0
        else:
            m_diaria = float(mv.valor_meta) / len(dias_uteis_lista) if dias_uteis_lista else 0
            
        if m_diaria < 0: m_diaria = 0
        
        ranking.append({
            'id': mv.usuario_id,
            'nome': mv.usuario.nome,
            'meta': float(mv.valor_meta),
            'vendido': float(recebido_total),
            'perc': perc,
            'meta_diaria': m_diaria
        })
        
    ranking.sort(key=lambda x: x['perc'], reverse=True)

    return render_template('metas/painel.html', 
                           meta_loja=meta_config,
                           vendido_loja=total_recebido_loja,
                           perc_loja=perc_loja,
                           ranking=ranking,
                           calendario=calendario_dados,
                           meta_diaria_loja=meta_diaria_hoje,
                           fmt_moeda=fmt_moeda,
                           mes_atual=mes_atual,
                           ano_atual=ano_atual)

# API Detalhes (Mantida igual)
@bp_metas.route('/api/vendas-usuario/<int:usuario_id>', methods=['GET'])
@login_required
def api_vendas_usuario(usuario_id):
    try:
        mes = int(request.args.get('mes'))
        ano = int(request.args.get('ano'))
        
        # BUSCA NOS PAGAMENTOS: 
        # Filtramos pela data_pagamento e não mais pela data da venda
        pagamentos = Pagamento.query.join(Venda).filter(
            Venda.vendedor_id == usuario_id,
            extract('month', Pagamento.data_pagamento) == mes,
            extract('year', Pagamento.data_pagamento) == ano
        ).order_by(Pagamento.data_pagamento.desc()).all()
        
        dados = []
        for p in pagamentos:
            dados.append({
                'id': p.venda_id,
                # ALTERAÇÃO AQUI: data do pagamento formatada
                'data': p.data_pagamento.strftime('%d/%m/%Y %H:%M'), 
                'cliente': p.venda.cliente_nome,
                'valor': fmt_moeda(p.valor) # Valor da parcela/pagamento recebido
            })
            
        return jsonify({'vendas': dados})
    except Exception as e:
        return jsonify({'erro': str(e)}), 400