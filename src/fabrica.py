from flask import Flask, redirect, url_for
from flask_login import current_user
from src.configuracao import configuracoes
from src.extensoes import banco_de_dados, migracao, login_manager

def criar_app(nome_configuracao='desenvolvimento'):
    app = Flask(__name__)
    app.config.from_object(configuracoes[nome_configuracao])
    
    # Inicializar extensões
    banco_de_dados.init_app(app)
    migracao.init_app(app, banco_de_dados)
    login_manager.init_app(app)
    
    # --- REGISTRO DE BLUEPRINTS ---
    from src.modulos.autenticacao import bp_autenticacao
    app.register_blueprint(bp_autenticacao)

    from src.modulos.vendas.rotas import bp_vendas
    app.register_blueprint(bp_vendas)

    # REMOVIDO: from src.modulos.produtos.rotas import bp_produtos
    # REMOVIDO: app.register_blueprint(bp_produtos)

    from src.modulos.operacional.rotas import bp_operacional
    app.register_blueprint(bp_operacional)

    from src.modulos.financeiro.rotas import bp_financeiro
    app.register_blueprint(bp_financeiro)

    from src.modulos.metas.rotas import bp_metas
    app.register_blueprint(bp_metas)

    from src.modulos.dashboard import bp_dashboard
    app.register_blueprint(bp_dashboard)

    from src.modulos.estoque import bp_estoque
    app.register_blueprint(bp_estoque)
    
    # --- AUTOMATIZAÇÃO: Atualiza Permissões ao Iniciar ---
    with app.app_context():
        try:
            # Tenta criar tabelas se não existirem
            banco_de_dados.create_all()
            
            # Sincroniza e LIMPA permissões antigas
            sincronizar_modulos_oficiais()
        except Exception as e:
            print(f"Nota: Banco de dados ainda não pronto ou erro de conexão. ({e})")

    # --- ROTAS GERAIS ---
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.painel'))
        else:
            return redirect(url_for('autenticacao.login'))

    return app

def sincronizar_modulos_oficiais():
    """
    Função que garante que os módulos no banco sejam EXATAMENTE
    os definidos aqui. Remove os obsoletos.
    """
    from src.modulos.autenticacao.modelos import Modulo
    
    # LISTA OFICIAL DE PERMISSÕES (A ÚNICA VERDADE)
    modulos_oficiais = [
        # 1. Dashboard
        {'codigo': 'dash_financeiro',   'nome': 'Dashboard - Ver Financeiro (Caixa/Recebimentos)'},
        {'codigo': 'dash_despesas',     'nome': 'Dashboard - Ver Contas a Pagar/Alertas'},
        {'codigo': 'dash_performance',  'nome': 'Dashboard - Ver Performance (Metas/Ticket Médio)'},
        {'codigo': 'dash_operacional',  'nome': 'Dashboard - Ver Operacional (Produção/Fila)'},

        # 2. Vendas & Serviços
        {'codigo': 'vendas_operar',       'nome': 'Vendas - Criar/Editar Vendas'},
        {'codigo': 'vendas_ver_lista',    'nome': 'Vendas - Ver Lista de Serviços'},
        {'codigo': 'vendas_ver_valores',  'nome': 'Vendas - Ver Valores Financeiros'},
        {'codigo': 'vendas_ver_metricas', 'nome': 'Vendas - Ver Métricas de Produção'},

        # 3. Módulos de Gestão
        {'codigo': 'financeiro_acesso', 'nome': 'Financeiro - Acesso Completo'},
        {'codigo': 'producao_operar',   'nome': 'Produção - Painel Operacional'},
        {'codigo': 'estoque_gerir',     'nome': 'Estoque - Gestão de Produtos'},
        {'codigo': 'metas_equipe',      'nome': 'Metas - Acesso ao Painel'},
        
        # 4. RH
        {'codigo': 'rh_equipe',         'nome': 'RH - Gestão de Usuários'},
        {'codigo': 'rh_salarios',       'nome': 'RH - Ver Salários'}
    ]
    
    codigos_oficiais = [m['codigo'] for m in modulos_oficiais]
    alteracoes = False

    # 1. Cria ou Atualiza Novos
    for m_data in modulos_oficiais:
        mod_db = Modulo.query.filter_by(codigo=m_data['codigo']).first()
        if not mod_db:
            print(f"[Sistema] Criando novo módulo: {m_data['nome']}")
            novo = Modulo(nome=m_data['nome'], codigo=m_data['codigo'])
            banco_de_dados.session.add(novo)
            alteracoes = True
        elif mod_db.nome != m_data['nome']:
            mod_db.nome = m_data['nome']
            alteracoes = True
    
    # 2. LIMPEZA: Remove permissões que não estão na lista oficial
    # Isso vai apagar "Catálogo", "Vendas - Gestão/Preços" e qualquer outra coisa antiga.
    todos_db = Modulo.query.all()
    for m in todos_db:
        if m.codigo not in codigos_oficiais:
            print(f"[Sistema] Removendo módulo obsoleto: {m.nome} ({m.codigo})")
            # Remove associações com usuários primeiro (se o banco não tiver cascade)
            m.usuarios = [] 
            banco_de_dados.session.delete(m)
            alteracoes = True

    if alteracoes:
        banco_de_dados.session.commit()
        print("[Sistema] Permissões sincronizadas e limpas com sucesso.")