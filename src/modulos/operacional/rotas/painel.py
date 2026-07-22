from flask import render_template, url_for
from flask_login import login_required
from sqlalchemy.orm import joinedload # <--- NOVA IMPORTAÇÃO
from src.modulos.vendas.modelos import ItemVenda, Venda, hora_brasilia
from src.modulos.autenticacao.permissoes import cargo_exigido
from src.modulos.estoque.modelos import ProdutoEstoque
from . import bp_operacional

def calcular_tempo_decorrido(data_inicio):
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
    
    # 1. Busca ITENS (Vendas Múltiplas) - OTIMIZADO (Traz venda, produto, cor e fotos juntos)
    itens_multi = ItemVenda.query.join(Venda).filter(
        ItemVenda.status.in_(['pendente', 'producao', 'retrabalho', 'pronto']),
        Venda.status != 'cancelado',
        Venda.status != 'orcamento',
        Venda.modo == 'multipla'
    ).options(
        joinedload(ItemVenda.venda),
        joinedload(ItemVenda.produto),
        joinedload(ItemVenda.cor),
        joinedload(ItemVenda.fotos)
    ).all()

    # 2. Busca VENDAS SIMPLES - OTIMIZADO (Traz produto, cor e itens[com fotos] juntos)
    vendas_simples = Venda.query.filter(
        Venda.modo == 'simples',
        Venda.status.in_(['pendente', 'producao', 'retrabalho', 'pronto']),
        Venda.status != 'orcamento'
    ).options(
        joinedload(Venda.produto),
        joinedload(Venda.cor),
        joinedload(Venda.itens).joinedload(ItemVenda.fotos)
    ).all()
    
    tarefas = []

    # --- PROCESSAMENTO DE ITENS (Vendas Múltiplas) ---
    # Agrupa itens do mesmo venda_id + status + descricao em um único card
    grupos_multi = {}
    for i in itens_multi:
        chave = (i.venda_id, i.status, i.descricao, i.produto_id, i.cor_id)
        if chave not in grupos_multi:
            grupos_multi[chave] = []
        grupos_multi[chave].append(i)

    for chave, grupo in grupos_multi.items():
        # Usa o item de menor ID como âncora (recebe as ações de avançar/retrabalho)
        ancora = min(grupo, key=lambda x: x.id)
        v = ancora.venda

        nome_acabamento = '-'
        if ancora.produto: nome_acabamento = ancora.produto.nome
        elif ancora.cor: nome_acabamento = ancora.cor.nome

        # Soma quantidades e metragens de todos os fragmentos
        quantidade_total = sum(x.quantidade for x in grupo)
        metragem_total_grupo = sum(x.metragem_total or 0 for x in grupo)

        data_ref = v.criado_em
        tempo_label = "Tempo em Fila"
        if ancora.status == 'producao':
            data_ref = ancora.data_inicio_producao or v.criado_em
            tempo_label = "Tempo em Execução"
        elif ancora.status == 'retrabalho':
            data_ref = ancora.data_inicio_producao or v.criado_em
            tempo_label = "Tempo em Retrabalho"
        elif ancora.status == 'pronto':
            data_ref = ancora.data_pronto or v.criado_em
            tempo_label = "Tempo Aguardando"

        metragem_texto = "Não informada"
        if metragem_total_grupo and metragem_total_grupo > 0:
            un = "m³" if ancora.tipo_medida == 'm3' else "m²"
            metragem_texto = f"{float(metragem_total_grupo):.2f} {un}"

        fotos_urls = []
        for frag in grupo:
            if frag.fotos:
                fotos_urls += [url_for('vendas.imagem_db', foto_id=f.id) for f in frag.fotos]

        tarefas.append({
            'tipo': 'item',
            'id': ancora.id,
            'venda_id': ancora.venda_id,
            'descricao': ancora.descricao,
            'quantidade': quantidade_total,
            'cor': nome_acabamento,
            'status': ancora.status,
            'cliente': v.cliente_nome,
            'obs': v.observacoes_internas,
            'criado_em': v.criado_em,
            'is_producao': (ancora.status in ['producao', 'retrabalho']),
            'tempo_decorrido': calcular_tempo_decorrido(data_ref),
            'tempo_label': tempo_label,
            'metragem': metragem_texto,
            'prioridade': v.prioridade,
            'fotos': fotos_urls,
            'is_venda_simples': False
        })

    # --- PROCESSAMENTO DE VENDAS SIMPLES ---
    # Agrupa itens (fragmentados por retrabalho parcial) do mesmo venda_id + status
    for v in vendas_simples:
        nome_acabamento = 'Padrão'
        if v.produto: nome_acabamento = v.produto.nome
        elif v.cor: nome_acabamento = v.cor.nome

        # Agrupa os sub-itens por status
        grupos_status = {}
        for i in v.itens:
            if i.status not in grupos_status:
                grupos_status[i.status] = []
            grupos_status[i.status].append(i)

        for status, grupo in grupos_status.items():
            ancora = min(grupo, key=lambda x: x.id)

            # Soma quantidades de todos os fragmentos no mesmo status
            quantidade_total = sum(x.quantidade for x in grupo)

            data_ref = v.criado_em
            tempo_label = "Tempo em Fila"
            if status == 'producao':
                data_ref = ancora.data_inicio_producao or v.criado_em
                tempo_label = "Tempo em Execução"
            elif status == 'retrabalho':
                data_ref = ancora.data_inicio_producao or v.criado_em
                tempo_label = "Tempo em Retrabalho"
            elif status == 'pronto':
                data_ref = ancora.data_pronto or v.criado_em
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
                # Metragem proporcional ao total de peças neste grupo
                metragem_prop = (float(v.metragem_total) / (v.quantidade_pecas or 1)) * quantidade_total
                metragem_texto = f"{metragem_prop:.2f} {un} {dimensoes}"

            fotos_urls = []
            for frag in grupo:
                if frag.fotos:
                    fotos_urls += [url_for('vendas.imagem_db', foto_id=f.id) for f in frag.fotos]

            tarefas.append({
                'tipo': 'item',
                'id': ancora.id,
                'venda_id': v.id,
                'descricao': v.descricao_servico,
                'quantidade': quantidade_total,
                'cor': nome_acabamento,
                'status': status,
                'cliente': v.cliente_nome,
                'obs': v.observacoes_internas,
                'criado_em': v.criado_em,
                'is_producao': (status in ['producao', 'retrabalho']),
                'tempo_decorrido': calcular_tempo_decorrido(data_ref),
                'tempo_label': tempo_label,
                'metragem': metragem_texto,
                'prioridade': v.prioridade,
                'fotos': fotos_urls,
                'is_venda_simples': True
            })

    # Ordenação
    tarefas.sort(key=lambda x: (not x['prioridade'], not x['is_producao'], x['criado_em']))

    # Contadores
    qtd_fila = sum(1 for t in tarefas if t['status'] == 'pendente')
    qtd_producao = sum(1 for t in tarefas if t['status'] == 'producao')
    qtd_retrabalho = sum(1 for t in tarefas if t['status'] == 'retrabalho')
    qtd_pronto = sum(1 for t in tarefas if t['status'] == 'pronto')
    
    produtos_estoque = ProdutoEstoque.query.filter_by(ativo=True).order_by(ProdutoEstoque.nome).all()

    return render_template('operacional/painel.html', 
                           tarefas=tarefas,
                           qtd_fila=qtd_fila, 
                           qtd_producao=qtd_producao,
                           qtd_retrabalho=qtd_retrabalho,
                           qtd_pronto=qtd_pronto,
                           produtos_estoque=produtos_estoque)