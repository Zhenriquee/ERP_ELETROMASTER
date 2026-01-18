from flask import jsonify, request
from flask_login import login_required
from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import Venda, CorServico

# Importa o Blueprint da pasta atual
from . import bp_vendas

# --- API: BUSCAR CLIENTES (AUTOCOMPLETE) ---
@bp_vendas.route('/api/buscar-clientes')
@login_required
def buscar_clientes():
    termo = request.args.get('q', '').lower()
    
    # Busca nomes distintos de clientes que já compraram
    # Filtra por termo se fornecido (mínimo 2 letras)
    if len(termo) < 2:
        return jsonify([])

    # Consulta otimizada: Traz apenas nomes únicos que contém o termo
    clientes = db.session.query(Venda.cliente_nome, Venda.cliente_documento)\
        .filter(Venda.cliente_nome.ilike(f'%{termo}%'))\
        .distinct().limit(10).all()

    # Formata para JSON
    resultados = []
    for nome, doc in clientes:
        resultados.append({
            'nome': nome,
            'documento': doc or ''
        })
        
    return jsonify(resultados)

# --- API: BUSCAR PRODUTOS/SERVIÇOS (AUTOCOMPLETE) ---
@bp_vendas.route('/api/buscar-produtos')
@login_required
def buscar_produtos():
    termo = request.args.get('q', '').lower()
    
    # Busca cores/serviços ativos
    query = CorServico.query.filter_by(ativo=True)
    
    if termo:
        query = query.filter(CorServico.nome.ilike(f'%{termo}%'))
        
    produtos = query.limit(20).all()
    
    resultados = []
    for p in produtos:
        resultados.append({
            'id': p.id,
            'nome': p.nome,
            'preco': float(p.preco_unitario),
            'unidade': p.unidade_medida
        })
        
    return jsonify(resultados)