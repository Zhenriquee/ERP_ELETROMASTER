from flask import Flask, render_template, redirect, url_for
from flask_login import login_required, current_user
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
    
    # 1. Autenticação (Login, Users)
    from src.modulos.autenticacao import bp_autenticacao
    app.register_blueprint(bp_autenticacao)

    # 2. Vendas (Novo Módulo)
    from src.modulos.vendas.rotas import bp_vendas
    app.register_blueprint(bp_vendas)

    # 3. Produtos (Catálogo)
    from src.modulos.produtos.rotas import bp_produtos
    app.register_blueprint(bp_produtos)

    from src.modulos.operacional.rotas import bp_operacional
    app.register_blueprint(bp_operacional)

    # 5. FINANCEIRO (Adicione isto aqui!)
    # Como ainda não temos rotas, importamos apenas os modelos para o banco reconhecer
    from src.modulos.financeiro.rotas import bp_financeiro
    app.register_blueprint(bp_financeiro)

    from src.modulos.metas.rotas import bp_metas
    app.register_blueprint(bp_metas)

    # 6. DASHBOARD (Adicione isto!)
    from src.modulos.dashboard import bp_dashboard
    app.register_blueprint(bp_dashboard)
    
    # --- COMANDOS CLI (Terminal) ---

    @app.cli.command("criar-admin")
    def criar_admin():
        from src.modulos.autenticacao.modelos import Usuario, Modulo
        
        
        # 1. Cria Módulos do Sistema
        modulos = [
            {'nome': 'RH - Gestão de Equipe', 'codigo': 'rh_equipe'},
            {'nome': 'RH - Ver Salários', 'codigo': 'rh_salarios'},
            {'nome': 'Estoque - Visualizar', 'codigo': 'estoque_ver'},
            {'nome': 'Estoque - Movimentar', 'codigo': 'estoque_mover'},
            {'nome': 'Vendas - Operar', 'codigo': 'vendas_operar'},     # <-- Novo
            {'nome': 'Vendas - Gestão Preços', 'codigo': 'vendas_admin'}, # <-- Novo
            {'nome': 'Catálogo - Gestão', 'codigo': 'produtos_gerir'},
            {'nome': 'Operacional - Produção', 'codigo': 'producao_operar'}
        ]
        
        for m_data in modulos:
            if not Modulo.query.filter_by(codigo=m_data['codigo']).first():
                novo_m = Modulo(nome=m_data['nome'], codigo=m_data['codigo'])
                banco_de_dados.session.add(novo_m)
        
        banco_de_dados.session.commit()
        print("Módulos de sistema atualizados.")

        # 2. Cria Dono
        if not Usuario.query.filter_by(usuario='admin').first():
            u = Usuario(nome='Dono', usuario='admin', cargo='dono')
            u.definir_senha('admin123')
            banco_de_dados.session.add(u)
            banco_de_dados.session.commit()
            print("Admin criado.")

    @app.cli.command("seed-vendas")
    def seed_vendas():
        """Popula o banco com cores iniciais para teste"""
        from src.modulos.vendas.modelos import CorServico
        
        cores_iniciais = [
            {'nome': 'Branco Pintura Eletrostática', 'unidade': 'm2', 'preco': 45.00},
            {'nome': 'Preto Fosco', 'unidade': 'm2', 'preco': 55.00},
            {'nome': 'Cinza Industrial', 'unidade': 'm2', 'preco': 50.00},
            {'nome': 'Tanque (Imersão)', 'unidade': 'm3', 'preco': 120.00},
            {'nome': 'Verniz Protetor', 'unidade': 'm2', 'preco': 30.00},
        ]

        count = 0
        for c in cores_iniciais:
            if not CorServico.query.filter_by(nome=c['nome']).first():
                nova = CorServico(
                    nome=c['nome'], 
                    unidade_medida=c['unidade'], 
                    preco_unitario=c['preco']
                )
                banco_de_dados.session.add(nova)
                count += 1
        
        banco_de_dados.session.commit()
        print(f"Sucesso! {count} novas cores/serviços adicionados.")



    # --- ROTAS GERAIS ---

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            # Redireciona para o painel do dashboard
            return redirect(url_for('dashboard.painel'))
        else:
            return redirect(url_for('autenticacao.login'))

    # --- IMPORTANTE: Retorna o objeto app criado ---
    return app
 