from flask import jsonify, request, url_for
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


@bp_vendas.route('/api/servico/<int:id>/detalhes')
@login_required
def detalhes_servico(id):
    venda = Venda.query.get_or_404(id)
    
    # Lista de Itens com suas respectivas fotos aninhadas
    itens_dados = []
    
    for item in venda.itens:
        # 1. Processa fotos deste item específico
        fotos_item = []
        for foto in item.fotos:
            fotos_item.append({
                'id': foto.id,
                'url': url_for('vendas.imagem_db', foto_id=foto.id),
                'nome': foto.nome_arquivo
            })

        # 2. Monta o objeto do item
        itens_dados.append({
            'id': item.id,
            'descricao': item.descricao,
            'medidas': f"{float(venda.dimensao_1 or 0)} x {float(venda.dimensao_2 or 0)}" if venda.modo == 'simples' else "Sob Medida",
            'qtd': item.quantidade,
            'material': item.produto.nome if item.produto else (item.cor.nome if item.cor else '-'),
            'fotos': fotos_item # Fotos aninhadas aqui!
        })
            
    return jsonify({
        'id': venda.id,
        'modo': venda.modo,
        'observacoes': venda.observacoes_internas,
        'itens': itens_dados,
        # 'fotos': [] -> Removemos a lista global, agora está dentro de 'itens'
        'dimensao_1': float(venda.dimensao_1 or 0),
        'dimensao_2': float(venda.dimensao_2 or 0),
        'dimensao_3': float(venda.dimensao_3 or 0),
        'tipo_medida': venda.tipo_medida
    })