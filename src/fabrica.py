from flask import Flask
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
    # Certifique-se que a pasta src/modulos/autenticacao existe e tem o __init__.py
    from src.modulos.autenticacao import bp_autenticacao
    app.register_blueprint(bp_autenticacao)
    
    @app.cli.command("criar-admin")
    def criar_admin():
        from src.modulos.autenticacao.modelos import Usuario
        # Verifica se já existe
        usuario_existente = Usuario.query.filter_by(usuario='admin').first()
        if usuario_existente:
            print("AVISO: O Usuário Admin já existe.")
            return
            
        # Criação atualizada com o campo 'usuario'
        u = Usuario(
            nome='Dono do Sistema', 
            usuario='admin',  # <--- Login simples
            email='admin@eletromaster.com', # Opcional, mas bom ter
            cargo='dono'
        )
        u.definir_senha('admin123') 
        banco_de_dados.session.add(u)
        banco_de_dados.session.commit()
        print("SUCESSO: Usuário Admin criado! Login: admin / Senha: admin123")

    @app.route('/saude')
    def verificacao_saude():
        return {"status": "operacional", "ambiente": nome_configuracao}
        
    return app