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
    
    # Registrar Blueprints
    
    # --- MÓDULO ESTOQUE (DESATIVADO TEMPORARIAMENTE) ---
    # from src.modulos.estoque import bp_estoque
    # app.register_blueprint(bp_estoque)
    
    # --- MÓDULO AUTENTICAÇÃO (ATIVO) ---
    from src.modulos.autenticacao import bp_autenticacao
    app.register_blueprint(bp_autenticacao)
    
    # Comando CLI para criar Admin
    @app.cli.command("criar-admin")
    def criar_admin():
        from src.modulos.autenticacao.modelos import Usuario, Modulo
        
        # 1. Cria Módulos do Sistema
        modulos = [
            {'nome': 'RH - Gestão de Equipe', 'codigo': 'rh_equipe'},
            {'nome': 'RH - Ver Salários', 'codigo': 'rh_salarios'},
            {'nome': 'Estoque - Visualizar', 'codigo': 'estoque_ver'},
            {'nome': 'Estoque - Movimentar', 'codigo': 'estoque_mover'},
            {'nome': 'Financeiro - Acesso Total', 'codigo': 'financeiro_full'}
        ]
        
        for m_data in modulos:
            if not Modulo.query.filter_by(codigo=m_data['codigo']).first():
                novo_m = Modulo(nome=m_data['nome'], codigo=m_data['codigo'])
                banco_de_dados.session.add(novo_m)
        
        banco_de_dados.session.commit()
        print("Módulos de sistema criados.")

        # 2. Cria Dono (Igual antes)
        if not Usuario.query.filter_by(usuario='admin').first():
            u = Usuario(nome='Dono', usuario='admin', cargo='dono')
            u.definir_senha('admin123')
            banco_de_dados.session.add(u)
            banco_de_dados.session.commit()
            print("Admin criado.")

    # --- ROTA RAIZ (Redirecionamento Inteligente) ---
    @app.route('/')
    def index():
        # Se o usuário já estiver logado, manda para o Dashboard
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        # Se não estiver logado, manda para o Login
        else:
            return redirect(url_for('autenticacao.login'))

    # Rota do Dashboard
    @app.route('/dashboard')
    @login_required
    def dashboard():
        return render_template('dashboard.html')

    @app.route('/saude')
    def verificacao_saude():
        return {"status": "operacional", "ambiente": nome_configuracao}
        
    return app