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
    
    # --- COMANDOS CLI (Terminal) ---

    @app.cli.command("criar-admin")
    def criar_admin():
        from src.modulos.autenticacao.modelos import Usuario, Modulo
        
        print("--- INICIANDO ATUALIZAÇÃO DE MÓDULOS ---")

        # 1. LISTA OFICIAL E ÚNICA DE MÓDULOS (O que vale é isso aqui)
        # Qualquer coisa no banco que não esteja aqui será APAGADA.
        modulos_oficiais = [
            {'codigo': 'rh_equipe',         'nome': 'RH - Gestão de Equipe'},
            {'codigo': 'rh_salarios',       'nome': 'RH - Ver Salários'},
            {'codigo': 'vendas_operar',     'nome': 'Vendas - Realizar Vendas'},
            {'codigo': 'vendas_admin',      'nome': 'Vendas - Gestão/Preços'},
            {'codigo': 'produtos_gerir',    'nome': 'Catálogo - Gestão'},
            {'codigo': 'producao_operar',   'nome': 'Operacional - Produção'},
            {'codigo': 'metas_equipe',      'nome': 'Metas - Visualizar'},
            {'codigo': 'financeiro_acesso', 'nome': 'Financeiro - Acesso Completo'} 
        ]
        
        codigos_oficiais = [m['codigo'] for m in modulos_oficiais]

        # 2. LIMPEZA: Remove módulos que não existem mais (Estoque, Antigos, Duplicados)
        modulos_no_banco = Modulo.query.all()
        removidos = 0
        for mod_db in modulos_no_banco:
            if mod_db.codigo not in codigos_oficiais:
                print(f"REMOVENDO módulo obsoleto: {mod_db.nome} ({mod_db.codigo})")
                banco_de_dados.session.delete(mod_db)
                removidos += 1
        
        if removidos > 0:
            banco_de_dados.session.commit()
            print(f"Limpeza concluída. {removidos} módulos antigos removidos.")

        # 3. CRIAÇÃO/ATUALIZAÇÃO: Garante que os oficiais existam com o nome certo
        criados = 0
        atualizados = 0
        for m_data in modulos_oficiais:
            mod_existente = Modulo.query.filter_by(codigo=m_data['codigo']).first()
            
            if not mod_existente:
                # Cria se não existe
                novo_m = Modulo(nome=m_data['nome'], codigo=m_data['codigo'])
                banco_de_dados.session.add(novo_m)
                criados += 1
            else:
                # Atualiza o nome se mudou (ex: corrigir Financeiro Total -> Completo)
                if mod_existente.nome != m_data['nome']:
                    mod_existente.nome = m_data['nome']
                    atualizados += 1

        banco_de_dados.session.commit()
        print(f"Sincronização finalizada: {criados} criados, {atualizados} nomes corrigidos.")

        # 4. GARANTIR ADMIN
        if not Usuario.query.filter_by(usuario='admin').first():
            u = Usuario(nome='Dono', usuario='admin', cargo='dono')
            u.definir_senha('admin123')
            banco_de_dados.session.add(u)
            banco_de_dados.session.commit()
            print("Usuário Admin criado com sucesso.")

    # --- ROTAS GERAIS ---

    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.painel'))
        else:
            return redirect(url_for('autenticacao.login'))

    return app