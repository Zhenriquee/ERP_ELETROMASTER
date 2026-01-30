import os
from datetime import timedelta # <--- IMPORTANTE: Adicione este import
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Carrega as variáveis do arquivo .env para a memória do sistema
load_dotenv()

class ConfiguracaoBase:
    SECRET_KEY = os.getenv('SECRET_KEY', 'chave_padrao_desenvolvimento_insegura')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    basedir = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(os.path.dirname(basedir), 'uploads_colaboradores')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # Limite de 16MB

    # --- CONFIGURAÇÃO DE TIMEOUT ---
    # Define que a sessão expira em 30 minutos
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=5)

class ConfiguracaoDesenvolvimento(ConfiguracaoBase):
    DEBUG = True
    
    # Captura os dados do .env
    db_usuario = os.getenv('DB_USUARIO', 'postgres')
    db_senha_bruta = os.getenv('DB_SENHA', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_nome = os.getenv('DB_NOME', 'erp_eletromaster_db')
    
    # TRATAMENTO DE SEGURANÇA:
    # A função quote_plus transforma caracteres especiais (como @) em formato seguro para URL (%40)
    # Isso evita que sua senha "quebre" a string de conexão
    db_senha_tratada = quote_plus(db_senha_bruta)
    
    # Monta a URL de conexão final usando f-string
    SQLALCHEMY_DATABASE_URI = f"postgresql://{db_usuario}:{db_senha_tratada}@{db_host}:5432/{db_nome}"

class ConfiguracaoProducao(ConfiguracaoBase):
    DEBUG = False
    # Em produção, geralmente a URL completa vem pronta do provedor de nuvem
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

configuracoes = {
    'desenvolvimento': ConfiguracaoDesenvolvimento,
    'producao': ConfiguracaoProducao
}