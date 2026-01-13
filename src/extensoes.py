from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Instâncias
banco_de_dados = SQLAlchemy()
migracao = Migrate()
login_manager = LoginManager()

# Configuração do Login
login_manager.login_view = 'autenticacao.login' # Nome da rota de login
login_manager.login_message = "Por favor, faça login para acessar esta página."
login_manager.login_message_category = "info"