# src/modulos/metas/rotas/monitoramento.py

from flask import render_template, request, jsonify
from flask_login import login_required
from datetime import date
from sqlalchemy import func
import calendar

from src.extensoes import banco_de_dados as db
from src.modulos.metas.modelos import MetaMensal, MetaVendedor
from src.modulos.vendas.modelos import Venda
from . import bp_metas

def fmt_moeda(valor):
    if valor is None:
        valor = 0.0
    return f"{float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

@bp_metas.route('/', methods=['GET'])
@login_required
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
    total_vendido_loja = db.session.query(func.sum(Venda.valor_final))\
        .filter(
            func.extract('month', Venda.criado_em) == mes_atual,
            func.extract('year', Venda.criado_em) == ano_atual,
            Venda.status != 'cancelada', 
            Venda.status != 'orcamento'
        ).scalar() or 0
        
    perc_loja = (float(total_vendido_loja) / float(meta_config.valor_loja)) * 100
    
    # 2. CALENDÁRIO
    dias_trabalho = [int(d) for d in meta_config.config_semana.split(',')]
    feriados = []
    if meta_config.config_feriados:
        try:
            feriados = [int(d) for d in meta_config.config_feriados.replace('.',',').split(',') if d.strip().isdigit()]
        except:
            pass

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
    
    meta_diaria = float(meta_config.valor_loja) / meta_config.dias_uteis if meta_config.dias_uteis > 0 else 0
    
    calendario_dados = []
    cal = calendar.monthcalendar(ano_atual, mes_atual)
    
    eh_mes_passado = (ano_atual < hoje.year) or (ano_atual == hoje.year and mes_atual < hoje.month)
    
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
            elif (ano_atual == hoje.year and mes_atual == hoje.month):
                eh_futuro = dia_numero > hoje.day
            else:
                eh_futuro = True
            
            # Objeto de informações do dia
            info = {
                'dia': dia_numero,
                'tipo': 'padrao',
                'vendido': mapa_vendas.get(dia_numero, 0),
                'meta_batida': False,
                'futuro': eh_futuro,
                'classe_cor_texto': 'text-gray-800' # Cor padrão
            }
            
            if eh_feriado:
                info['tipo'] = 'feriado'
            elif not eh_trabalho:
                info['tipo'] = 'folga'
            else:
                info['tipo'] = 'trabalho'
                if not info['futuro']:
                    meta_batida = info['vendido'] >= meta_diaria
                    info['meta_batida'] = meta_batida
                    
                    # --- LÓGICA DE COR MOVIDA PARA CÁ ---
                    if meta_batida:
                        info['classe_cor_texto'] = 'text-green-700'
                    else:
                        info['classe_cor_texto'] = 'text-red-700'
            
            semana_dados.append(info)
        calendario_dados.append(semana_dados)

    # 3. RANKING
    metas_vendedores = MetaVendedor.query.filter_by(meta_mensal_id=meta_config.id).all()
    ranking = []
    
    for mv in metas_vendedores:
        vendido = db.session.query(func.sum(Venda.valor_final))\
            .filter(
                Venda.vendedor_id == mv.usuario_id,
                func.extract('month', Venda.criado_em) == mes_atual,
                func.extract('year', Venda.criado_em) == ano_atual,
                Venda.status != 'cancelada',
                Venda.status != 'orcamento'
            ).scalar() or 0
            
        perc = (float(vendido) / float(mv.valor_meta)) * 100 if mv.valor_meta > 0 else 0
        m_diaria = float(mv.valor_meta) / meta_config.dias_uteis if meta_config.dias_uteis > 0 else 0
        
        ranking.append({
            'id': mv.usuario_id,
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
                           meta_diaria_loja=meta_diaria,
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
        
        vendas = Venda.query.filter(
            Venda.vendedor_id == usuario_id,
            func.extract('month', Venda.criado_em) == mes,
            func.extract('year', Venda.criado_em) == ano,
            Venda.status != 'cancelada',
            Venda.status != 'orcamento'
        ).order_by(Venda.criado_em.desc()).all()
        
        dados = []
        for v in vendas:
            dados.append({
                'id': v.id,
                'data': v.criado_em.strftime('%d/%m/%Y %H:%M'),
                'cliente': v.cliente_nome,
                'valor': fmt_moeda(v.valor_final)
            })
            
        return jsonify({'vendas': dados})
    except Exception as e:
        return jsonify({'erro': str(e)}), 400