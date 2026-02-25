import os
import requests
import hmac
import hashlib
import json
import time
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta
from flask import Flask, redirect, url_for, request, render_template, session # <--- ADICIONE session AQUI
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

    # --- NOVOS MÓDULOS REGISTRADOS ---
    from src.modulos.corporativo import bp_corporativo
    app.register_blueprint(bp_corporativo)

    from src.modulos.rh import bp_rh
    app.register_blueprint(bp_rh)

    # --- NOVO BLUEPRINT AQUI ---
    from src.modulos.relatorios import bp_relatorios
    app.register_blueprint(bp_relatorios)

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
        
    # 1. TIMEOUT DE SESSÃO (NOVO)
    @app.before_request
    def gerenciar_timeout():
        # Torna a sessão permanente para que o PERMANENT_SESSION_LIFETIME funcione
        session.permanent = True
        # O Flask atualiza o tempo de expiração automaticamente a cada requisição
        # se session.permanent for True.
        #     

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
    
    # LISTA OFICIAL DE PERMISSÕES 
    modulos_oficiais = [
        # 1. Dashboard (NOVO - ULTRA GRANULAR)
        {'codigo': 'dash_ind_receita', 'nome': 'Dashboard - Caixa & Recebíveis', 'descricao': 'Visualizar os cards de valores Recebidos no Mês e A Receber Geral.'},
        {'codigo': 'dash_ind_vendas', 'nome': 'Dashboard - Performance de Vendas', 'descricao': 'Visualizar a meta do mês, atingimento e os cards de vendas/recebimentos de hoje.'},
        {'codigo': 'dash_ind_pagar', 'nome': 'Dashboard - Contas a Pagar', 'descricao': 'Visualizar o card resumido de saídas financeiras do mês selecionado.'},
        {'codigo': 'dash_ind_alertas', 'nome': 'Dashboard - Alertas de Contas', 'descricao': 'Visualizar os alertas de despesas vencidas e as que vencem nos próximos 5 dias.'},
        {'codigo': 'dash_graf_fluxo', 'nome': 'Dashboard - Gráfico de Fluxo', 'descricao': 'Visualizar o gráfico de linhas de receitas e despesas (Semestral).'},
        {'codigo': 'dash_graf_custos', 'nome': 'Dashboard - Gráfico de Custos', 'descricao': 'Visualizar o gráfico de rosca com a divisão de despesas por categoria.'},
        {'codigo': 'dash_top_produtos', 'nome': 'Dashboard - Top Produtos', 'descricao': 'Visualizar o ranking dos 5 produtos mais vendidos nos últimos 30 dias.'},
        {'codigo': 'dash_ind_producao', 'nome': 'Dashboard - Fila de Produção', 'descricao': 'Visualizar os contadores de itens na Fila, Produção, Retrabalho, Prontos e Finalizados.'},
        
        # 2. Ponto de Venda (Criação)
        {'codigo': 'venda_criar', 'nome': 'Vendas - Realizar Venda', 'descricao': 'Acesso às telas de Nova Venda Simples e Múltipla.'},
        {'codigo': 'venda_desconto', 'nome': 'Vendas - Aplicar Desconto', 'descricao': 'Permite aplicar descontos em Reais ou Porcentagem na criação da venda.'},
        {'codigo': 'venda_imprimir', 'nome': 'Vendas - Imprimir Orçamento', 'descricao': 'Permite gerar o PDF do orçamento antes de finalizar a venda.'},
        
        # 3. Gestão de Serviços (Acompanhamento)
        {'codigo': 'gestao_acesso', 'nome': 'Gestão - Ver Lista', 'descricao': 'Visualizar a tabela principal de serviços em andamento.'},
        {'codigo': 'gestao_editar', 'nome': 'Gestão - Mudar Status', 'descricao': 'Permite alterar o andamento do serviço e adicionar fotos técnicas.'},
        {'codigo': 'gestao_cancelar', 'nome': 'Gestão - Cancelar Serviço', 'descricao': 'Permite cancelar pedidos da lista e estornar estoque.'},
        {'codigo': 'gestao_financeiro', 'nome': 'Gestão - Financeiro da Venda', 'descricao': 'Ver valores na lista, registrar pagamentos e acessar a aba de cobrança.'},
        {'codigo': 'gestao_metricas', 'nome': 'Gestão - Indicadores de Fila', 'descricao': 'Visualizar os cards de contagem (Fila, Produção, Pronto) no topo da tela.'},

        # 4. Módulos de Gestão (Serão refatorados depois)
        {'codigo': 'financeiro_acesso', 'nome': 'Financeiro - Acesso Completo', 'descricao': 'Acesso total à criação, edição e baixa de despesas.'},
        {'codigo': 'financeiro_ver_totais', 'nome': 'Financeiro - Ver Totais (Cards)', 'descricao': 'Visualizar os cards somatórios no topo da tela do financeiro.'},
        {'codigo': 'producao_operar', 'nome': 'Produção - Painel Operacional', 'descricao': 'Acesso à tela da linha de produção (Kanban/Listas).'},
        {'codigo': 'estoque_gerir', 'nome': 'Estoque - Gestão de Produtos', 'descricao': 'Criar produtos, editar preços e movimentar estoque manualmente.'},
        {'codigo': 'metas_equipe', 'nome': 'Metas - Acesso ao Painel', 'descricao': 'Visualizar e configurar metas mensais da loja e equipe.'},
        
        # 5. RH (Serão refatorados depois)
        {'codigo': 'rh_equipe', 'nome': 'RH - Gestão de Usuários', 'descricao': 'Cadastrar colaboradores, gerenciar acessos e editar perfis.'},
        {'codigo': 'rh_salarios', 'nome': 'RH - Ver Salários', 'descricao': 'Permissão para visualizar o valor do salário base no cadastro do RH.'},

        # 6. Relatórios
        {'codigo': 'relatorios_servicos', 'nome': 'Relatórios - Serviços Solicitados', 'descricao': 'Gerar e exportar planilhas de serviços e itens.'},
        {'codigo': 'relatorios_consumo', 'nome': 'Relatórios - Consumo de Materiais', 'descricao': 'Gerar e exportar relatórios de consumo de estoque.'},
        {'codigo': 'relatorios_financeiro', 'nome': 'Relatórios - Financeiro', 'descricao': 'Gerar relatórios de contas a pagar e fluxo de caixa.'}
    ]
    
    codigos_oficiais = [m['codigo'] for m in modulos_oficiais]
    alteracoes = False

    for m_data in modulos_oficiais:
        mod_db = Modulo.query.filter_by(codigo=m_data['codigo']).first()
        if not mod_db:
            novo = Modulo(nome=m_data['nome'], codigo=m_data['codigo'], descricao=m_data.get('descricao', ''))
            banco_de_dados.session.add(novo)
            alteracoes = True
        else:
            # Atualiza nome e descrição se tiverem mudado
            if mod_db.nome != m_data['nome'] or mod_db.descricao != m_data.get('descricao', ''):
                mod_db.nome = m_data['nome']
                mod_db.descricao = m_data.get('descricao', '')
                alteracoes = True
    
    todos_db = Modulo.query.all()
    for m in todos_db:
        if m.codigo not in codigos_oficiais:
            m.usuarios = [] 
            banco_de_dados.session.delete(m)
            alteracoes = True

    if alteracoes:
        banco_de_dados.session.commit()