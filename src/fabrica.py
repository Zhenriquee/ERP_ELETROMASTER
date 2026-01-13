from flask import Flask
from src.configuracao import configuracoes
from src.extensoes import banco_de_dados

def criar_app(nome_configuracao='desenvolvimento'):
    """
    Função Factory que cria e configura a instância da aplicação Flask.
    """
    app = Flask(__name__)
    
    # Carregar configurações
    app.config.from_object(configuracoes[nome_configuracao])
    
    # Inicializar extensões
    banco_de_dados.init_app(app)
    
    # Registrar Blueprints (Módulos) - Faremos isso em breve
    # from src.modulos.estoque.rotas import bp_estoque
    # app.register_blueprint(bp_estoque)
    
    @app.route('/saude')
    def verificacao_saude():
        return {"status": "operacional", "ambiente": nome_configuracao}
        
    return app