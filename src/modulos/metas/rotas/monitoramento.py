# src/modulos/metas/rotas/monitoramento.py

from flask import render_template
from flask_login import login_required
from datetime import date
from sqlalchemy import func
import calendar

from src.extensoes import banco_de_dados as db
from src.modulos.metas.modelos import MetaMensal, MetaVendedor
from src.modulos.vendas.modelos import Venda
from . import bp_metas

# --- FUNÇÃO AUXILIAR DE FORMATAÇÃO ---
def fmt_moeda(valor):
    if valor is None:
        valor = 0.0
    # Formata float para string "10.000,00" (Padrão BR)
    return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@bp_metas.route('/', methods=['GET'])
@login_required
def painel():
    hoje = date.today()
    mes_atual = hoje.month
    ano_atual = hoje.year
    
    meta_config = MetaMensal.query.filter_by(mes=mes_atual, ano=ano_atual).first()
    
    if not meta_config:
        return render_template('metas/sem_meta.html')

    # 1. DADOS GERAIS DA LOJA
    # CORREÇÃO 1: Venda.criado_em em vez de data_venda
    # CORREÇÃO 2: Venda.valor_final em vez de valor_total
    total_vendido_loja = db.session.query(func.sum(Venda.valor_final))\
        .filter(
            func.extract('month', Venda.criado_em) == mes_atual,
            func.extract('year', Venda.criado_em) == ano_atual,
            Venda.status != 'cancelada', 
            Venda.status != 'orcamento'
        ).scalar() or 0
        
    perc_loja = (float(total_vendido_loja) / float(meta_config.valor_loja)) * 100
    
    # 2. CALENDÁRIO DE PERFORMANCE
    dias_trabalho = [int(d) for d in meta_config.config_semana.split(',')]
    feriados = []
    if meta_config.config_feriados:
        try:
            feriados = [int(d) for d in meta_config.config_feriados.replace('.',',').split(',') if d.strip().isdigit()]
        except:
            pass

    # CORREÇÃO 1: Venda.criado_em em vez de data_venda
    # CORREÇÃO 2: Venda.valor_final em vez de valor_total
    vendas_diarias = db.session.query(
            func.extract('day', Venda.criado_em).label('dia'),
            func.sum(Venda.valor_final).label('total')
        ).filter(
            func.extract('month', Venda.criado_em) == mes_atual,
            func.extract('year', Venda.criado_em) == ano_atual,
            Venda.status != 'cancelada',
            Venda.status != 'orcamento'
        ).group_by('dia').all()
    
    mapa_vendas = {int(v.dia): float(v.total) for v in vendas_diarias}
    
    # Meta Diária Ideal
    meta_diaria = float(meta_config.valor_loja) / meta_config.dias_uteis if meta_config.dias_uteis > 0 else 0
    
    calendario_dados = []
    cal = calendar.monthcalendar(ano_atual, mes_atual)
    
    for semana in cal:
        semana_dados = []
        for dia_idx, dia_numero in enumerate(semana):
            if dia_numero == 0:
                semana_dados.append({'tipo': 'vazio'})
                continue
                
            eh_feriado = dia_numero in feriados
            eh_trabalho = dia_idx in dias_trabalho
            
            info = {
                'dia': dia_numero,
                'tipo': 'padrao',
                'vendido': mapa_vendas.get(dia_numero, 0),
                'meta_batida': False,
                'futuro': dia_numero > hoje.day
            }
            
            if eh_feriado:
                info['tipo'] = 'feriado'
            elif not eh_trabalho:
                info['tipo'] = 'folga'
            else:
                info['tipo'] = 'trabalho'
                if not info['futuro']:
                    info['meta_batida'] = info['vendido'] >= meta_diaria
            
            semana_dados.append(info)
        calendario_dados.append(semana_dados)

    # 3. RANKING DE VENDEDORES
    metas_vendedores = MetaVendedor.query.filter_by(meta_mensal_id=meta_config.id).all()
    ranking = []
    for mv in metas_vendedores:
        # CORREÇÃO 1: Venda.criado_em em vez de data_venda
        # CORREÇÃO 2: Venda.valor_final em vez de valor_total
        vendido = db.session.query(func.sum(Venda.valor_final))\
            .filter(
                Venda.vendedor_id == mv.usuario_id,
                func.extract('month', Venda.criado_em) == mes_atual,
                func.extract('year', Venda.criado_em) == ano_atual,
                Venda.status != 'cancelada'
            ).scalar() or 0
            
        perc = (float(vendido) / float(mv.valor_meta)) * 100 if mv.valor_meta > 0 else 0
        m_diaria = float(mv.valor_meta) / meta_config.dias_uteis if meta_config.dias_uteis > 0 else 0
        
        ranking.append({
            'nome': mv.usuario.nome,
            'meta': float(mv.valor_meta),
            'vendido': float(vendido),
            'perc': perc,
            'meta_diaria': m_diaria
        })
    ranking.sort(key=lambda x: x['perc'], reverse=True)

    return render_template('metas/painel.html', 
                           meta_loja=meta_config,
                           vendido_loja=total_vendido_loja,
                           perc_loja=perc_loja,
                           ranking=ranking,
                           calendario=calendario_dados,
                           meta_diaria_loja=meta_diaria)