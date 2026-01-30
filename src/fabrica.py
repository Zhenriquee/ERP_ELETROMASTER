import os
import requests
import hmac
import hashlib
import json
import time
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from flask import Flask, redirect, url_for, request, render_template
from flask_login import current_user
from src.configuracao import configuracoes
from src.extensoes import banco_de_dados, migracao, login_manager


# --- CONFIGURAÇÕES DO SISTEMA DE LICENÇA ---
# URL "Raw" do seu Gist (Substitua pelo seu link real)
URL_GIST = "https://gist.githubusercontent.com/Zhenriquee/1aa33c7f49b9871419411214002e33f1/raw/config.json"
# Nome do arquivo local que guardará a licença
ARQUIVO_LICENCA = 'license.key'


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

    @app.cli.command("backup")
    def comando_backup():
        """Executa backup rotativo (dias 1, 10, 20) para nuvem."""
        from src.backup_cloud import realizar_backup_nuvem
        realizar_backup_nuvem()

    # =========================================================
    # --- FUNÇÕES DE SEGURANÇA E LICENÇA ---
    # =========================================================
    def assinar_dados(dados_str):
        """Gera uma assinatura HMAC para proteger o arquivo local"""
        chave = app.config['SECRET_KEY'].encode('utf-8')
        msg = dados_str.encode('utf-8')
        return hmac.new(chave, msg, hashlib.sha256).hexdigest()

    def salvar_licenca_offline(data_validade):
        """Grava a data de validade + assinatura no disco"""
        data_str = data_validade.strftime('%Y-%m-%d')
        assinatura = assinar_dados(data_str)
        caminho = os.path.join(app.root_path, ARQUIVO_LICENCA)
        
        with open(caminho, 'w') as f:
            f.write(f"{data_str}|{assinatura}")

    def validar_licenca_local():
        """Verifica se o arquivo local é válido e não expirou"""
        caminho = os.path.join(app.root_path, ARQUIVO_LICENCA)
        if not os.path.exists(caminho):
            return False
        
        try:
            with open(caminho, 'r') as f:
                conteudo = f.read().strip()
                
            if '|' not in conteudo: return False
            
            data_str, assinatura_lida = conteudo.split('|')
            
            # 1. Checa adulteração
            assinatura_real = assinar_dados(data_str)
            if not hmac.compare_digest(assinatura_lida, assinatura_real):
                return False
            
            # 2. Checa data
            validade = datetime.strptime(data_str, '%Y-%m-%d').date()
            if date.today() <= validade:
                return True
            else:
                return False # Expirou
        except:
            return False

    def tentar_renovar_online():
        """Conecta no Gist para tentar renovar a licença"""
        try:
            # --- CORREÇÃO DE CACHE ---
            # Adiciona um timestamp aleatório no final da URL para obrigar
            # o servidor a baixar a versão nova e não a versão em cache.
            url_fresca = f"{URL_GIST}?v={int(time.time())}"
            
            print(f"Consultando Licença em: {url_fresca}") # Log para debug
            
            response = requests.get(url_fresca, timeout=5)
            
            if response.status_code == 200:
                dados = response.json()
                status = dados.get('status', 'bloqueado').lower()
                
                print(f"Status Recebido: {status}") # Log para debug

                if status == 'ativo':
                    # Renovação: Validade até o final do PRÓXIMO mês
                    hoje = date.today()
                    proximo_mes = hoje + relativedelta(months=2)
                    data_limite = proximo_mes.replace(day=1) - timedelta(days=1)
                    
                    salvar_licenca_offline(data_limite)
                    return True
                else:
                    # Se estiver bloqueado no Gist, remove a licença local
                    caminho = os.path.join(app.root_path, ARQUIVO_LICENCA)
                    if os.path.exists(caminho):
                        os.remove(caminho)
                    return False
            return False
        except Exception as e:
            print(f"Erro na renovação online: {e}")
            return False # Sem internet ou erro

    # --- MIDDLEWARE: EXECUTA A CADA REQUISIÇÃO ---
    @app.before_request
    def verificar_acesso():
        rota = request.endpoint
        # Libera arquivos estáticos e a própria tela de bloqueio
        if rota and ('static' in rota or 'sistema_suspenso' in rota):
            return None

        # 1. Tenta validar localmente (Rápido e Offline)
        if validar_licenca_local():
            return None # Acesso Liberado
        
        # 2. Se falhou (expirou ou não existe), tenta renovar online
        if tentar_renovar_online():
            return None # Renovou e liberou
        
        # 3. Se tudo falhou -> Bloqueia
        return redirect(url_for('autenticacao.sistema_suspenso'))
    
    # =========================================================
    # --- INICIALIZAÇÃO DO SISTEMA ---
    # =========================================================
    
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