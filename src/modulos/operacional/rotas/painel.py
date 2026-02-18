from flask import render_template, url_for
from flask_login import login_required
from src.modulos.vendas.modelos import ItemVenda, Venda, hora_brasilia
from src.modulos.autenticacao.permissoes import cargo_exigido
from src.modulos.estoque.modelos import ProdutoEstoque
from . import bp_operacional

def calcular_tempo_decorrido(data_inicio):
    """Retorna string amigável: '2d 4h' ou '35m'"""
    if not data_inicio:
        return "-"
    
    agora = hora_brasilia()
    if data_inicio.tzinfo: data_inicio = data_inicio.replace(tzinfo=None)
    if agora.tzinfo: agora = agora.replace(tzinfo=None)
        
    diff = agora - data_inicio
    dias = diff.days
    segundos = diff.seconds
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    
    if dias > 0: return f"{dias}d {horas}h"
    elif horas > 0: return f"{horas}h {minutos}m"
    else: return f"{minutos}m"

@bp_operacional.route('/painel')
@login_required
@cargo_exigido('producao_operar')
def painel():
    
    # 1. Busca ITENS (Vendas Múltiplas) - Adicionado 'retrabalho'
    itens_multi = ItemVenda.query.join(Venda).filter(
        ItemVenda.status.in_(['pendente', 'producao', 'retrabalho', 'pronto']),
        Venda.status != 'cancelado',
        Venda.status != 'orcamento',
        Venda.modo == 'multipla'
    ).all()

    # 2. Busca VENDAS SIMPLES - Adicionado 'retrabalho'
    vendas_simples = Venda.query.filter(
        Venda.modo == 'simples',
        Venda.status.in_(['pendente', 'producao', 'retrabalho', 'pronto']),
        Venda.status != 'orcamento'
    ).all()

    tarefas = []

    # --- PROCESSAMENTO DE ITENS ---
    for i in itens_multi:
        nome_acabamento = '-'
        if i.produto: nome_acabamento = i.produto.nome
        elif i.cor: nome_acabamento = i.cor.nome

        data_ref = i.venda.criado_em
        tempo_label = "Tempo em Fila"
        
        # Lógica de Tempo para Retrabalho
        if i.status == 'producao':
            data_ref = i.data_inicio_producao or i.venda.criado_em
            tempo_label = "Tempo em Execução"
        elif i.status == 'retrabalho':
            # Usa data de início de produção ou a última ação
            data_ref = i.data_inicio_producao or i.venda.criado_em
            tempo_label = "Tempo em Retrabalho"
        elif i.status == 'pronto':
            data_ref = i.data_pronto or i.venda.criado_em
            tempo_label = "Tempo Aguardando"

        metragem_texto = "Não informada"
        if i.metragem_total and i.metragem_total > 0:
            un = "m³" if i.tipo_medida == 'm3' else "m²"
            metragem_texto = f"{float(i.metragem_total):.2f} {un}"

        fotos_urls = []
        if i.fotos:
            fotos_urls = [url_for('vendas.imagem_db', foto_id=f.id) for f in i.fotos]
            
        tarefas.append({
            'tipo': 'item',
            'id': i.id,
            'venda_id': i.venda_id,
            'descricao': i.descricao,
            'quantidade': i.quantidade,
            'cor': nome_acabamento,
            'status': i.status,
            'cliente': i.venda.cliente_nome,
            'obs': i.venda.observacoes_internas,
            'criado_em': i.venda.criado_em,
            'is_producao': (i.status in ['producao', 'retrabalho']), # Considera retrabalho como produção ativa
            'tempo_decorrido': calcular_tempo_decorrido(data_ref),
            'tempo_label': tempo_label,
            'metragem': metragem_texto,
            'prioridade': i.venda.prioridade,
            'fotos': fotos_urls
        })

    # --- PROCESSAMENTO DE VENDAS SIMPLES ---
    for v in vendas_simples:
        nome_acabamento = 'Padrão'
        if v.produto: nome_acabamento = v.produto.nome
        elif v.cor: nome_acabamento = v.cor.nome

        data_ref = v.criado_em
        tempo_label = "Tempo em Fila"
        
        if v.status == 'producao':
            data_ref = v.data_inicio_producao or v.criado_em
            tempo_label = "Tempo em Execução"
        elif v.status == 'retrabalho':
            data_ref = v.data_inicio_producao or v.criado_em
            tempo_label = "Tempo em Retrabalho"
        elif v.status == 'pronto':
            data_ref = v.data_pronto or v.criado_em
            tempo_label = "Tempo Aguardando"

        dimensoes = ""
        if v.dimensao_1 and v.dimensao_2:
            if v.tipo_medida == 'm3' and v.dimensao_3:
                dimensoes = f"({float(v.dimensao_1)} x {float(v.dimensao_2)} x {float(v.dimensao_3)})"
            else:
                dimensoes = f"({float(v.dimensao_1)} x {float(v.dimensao_2)})"
        
        metragem_texto = "Não informada"
        if v.metragem_total and v.metragem_total > 0:
            un = "m³" if v.tipo_medida == 'm3' else "m²"
            metragem_texto = f"{float(v.metragem_total):.2f} {un} {dimensoes}"

        fotos_urls = []
        if v.itens and v.itens[0].fotos:
            fotos_urls = [url_for('vendas.imagem_db', foto_id=f.id) for f in v.itens[0].fotos]
            
        tarefas.append({
            'tipo': 'venda',
            'id': v.id,
            'venda_id': v.id,
            'item_unico_id': v.itens[0].id if v.itens else None,
            'descricao': v.descricao_servico,
            'quantidade': v.quantidade_pecas,
            'cor': nome_acabamento,
            'status': v.status,
            'cliente': v.cliente_nome,
            'obs': v.observacoes_internas,
            'criado_em': v.criado_em,
            'is_producao': (v.status in ['producao', 'retrabalho']),
            'tempo_decorrido': calcular_tempo_decorrido(data_ref),
            'tempo_label': tempo_label,
            'metragem': metragem_texto,
            'prioridade': v.prioridade,
            'fotos': fotos_urls
        })

    # Ordenação
    tarefas.sort(key=lambda x: (not x['prioridade'], not x['is_producao'], x['criado_em']))

    # Contadores
    qtd_fila = sum(1 for t in tarefas if t['status'] == 'pendente')
    qtd_producao = sum(1 for t in tarefas if t['status'] == 'producao')
    qtd_retrabalho = sum(1 for t in tarefas if t['status'] == 'retrabalho') # NOVO
    qtd_pronto = sum(1 for t in tarefas if t['status'] == 'pronto')
    
    produtos_estoque = ProdutoEstoque.query.filter_by(ativo=True).order_by(ProdutoEstoque.nome).all()

    return render_template('operacional/painel.html', 
                           tarefas=tarefas,
                           qtd_fila=qtd_fila, 
                           qtd_producao=qtd_producao,
                           qtd_retrabalho=qtd_retrabalho, # Passando novo contador
                           qtd_pronto=qtd_pronto,
                           produtos_estoque=produtos_estoque)