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

    from src.modulos.produtos.rotas import bp_produtos
    app.register_blueprint(bp_produtos)

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
            # Tenta criar tabelas se não existirem (segurança para dev)
            banco_de_dados.create_all()
            
            # Sincroniza os módulos novos automaticamente
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
    Função que garante que todos os módulos definidos no código 
    existam no banco de dados.
    """
    from src.modulos.autenticacao.modelos import Modulo
    
    # LISTA OFICIAL DE PERMISSÕES
    modulos_oficiais = [
        # 1. Dashboard (Novos que estavam faltando)
        {'codigo': 'dash_financeiro',   'nome': 'Dashboard - Ver Financeiro'},
        {'codigo': 'dash_despesas',     'nome': 'Dashboard - Ver Contas/Alertas'},
        {'codigo': 'dash_performance',  'nome': 'Dashboard - Ver Performance'},
        {'codigo': 'dash_operacional',  'nome': 'Dashboard - Ver Operacional'},

        # 2. Vendas & Serviços
        {'codigo': 'vendas_operar',       'nome': 'Vendas - Criar/Editar'},
        {'codigo': 'vendas_ver_lista',    'nome': 'Vendas - Ver Lista Serviços'},
        {'codigo': 'vendas_ver_valores',  'nome': 'Vendas - Ver Valores ($)'},
        {'codigo': 'vendas_ver_metricas', 'nome': 'Vendas - Ver Métricas'},

        # 3. Módulos de Gestão
        {'codigo': 'financeiro_acesso', 'nome': 'Financeiro - Acesso Completo'},
        {'codigo': 'producao_operar',   'nome': 'Produção - Painel Operacional'},
        {'codigo': 'estoque_gerir',     'nome': 'Estoque - Gestão de Produtos'},
        {'codigo': 'estoque_gerir',     'nome': 'Estoque - Gestão de Produtos'},
        {'codigo': 'metas_equipe',      'nome': 'Metas - Acesso ao Painel'},
        
        # 4. RH
        {'codigo': 'rh_equipe',         'nome': 'RH - Gestão de Equipe'},
        {'codigo': 'rh_salarios',       'nome': 'RH - Ver Salários'}
    ]
    
    codigos_no_codigo = [m['codigo'] for m in modulos_oficiais]
    alteracoes = False

    # 1. Cria ou Atualiza
    for m_data in modulos_oficiais:
        mod_db = Modulo.query.filter_by(codigo=m_data['codigo']).first()
        if not mod_db:
            print(f"[Sistema] Criando novo módulo de permissão: {m_data['nome']}")
            novo = Modulo(nome=m_data['nome'], codigo=m_data['codigo'])
            banco_de_dados.session.add(novo)
            alteracoes = True
        elif mod_db.nome != m_data['nome']:
            mod_db.nome = m_data['nome']
            alteracoes = True
    
    # 2. (Opcional) Limpa antigos
    # Comentado para evitar apagar coisas por engano em produção, 
    # mas descomente se quiser limpar permissões velhas.
    # todos_db = Modulo.query.all()
    # for m in todos_db:
    #     if m.codigo not in codigos_no_codigo:
    #         banco_de_dados.session.delete(m)
    #         alteracoes = True

    if alteracoes:
        banco_de_dados.session.commit()
        print("[Sistema] Permissões sincronizadas com sucesso.")