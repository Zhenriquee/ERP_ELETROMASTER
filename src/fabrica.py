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
        {'codigo': 'venda_criar', 'nome': 'Nova Venda - Acesso ao Modulo', 'descricao': 'Acesso às telas de Nova Venda Simples e Múltipla.'},
        {'codigo': 'venda_desconto', 'nome': 'Nova Venda - Aplicar Desconto', 'descricao': 'Permite aplicar descontos em Reais ou Porcentagem na criação da venda.'},
        {'codigo': 'venda_imprimir', 'nome': 'Nova Venda - Imprimir Orçamento', 'descricao': 'Permite gerar o PDF do orçamento antes de finalizar a venda.'},
        
        # 3. Gestão de Serviços (Acompanhamento)
        {'codigo': 'gestao_acesso', 'nome': 'Gestão de Serviços - Acesso ao Modulo', 'descricao': 'Visualizar a tabela principal de serviços em andamento.'},
        {'codigo': 'gestao_ind_financeiro', 'nome': 'Gestão de Serviços - Cards Financeiros', 'descricao': 'Visualizar o Faturamento e Ticket Médio no topo da tela.'},
        {'codigo': 'gestao_ind_operacional', 'nome': 'Gestão de Serviços - Cards Operacionais', 'descricao': 'Visualizar a contagem de itens na Fila e Produção no topo.'},
        {'codigo': 'gestao_gerenciar', 'nome': 'Gestão de Serviços - Ver Detalhes (Modal)', 'descricao': 'Permite clicar no botão "Gerenciar" para ver a timeline e os itens.'},
        {'codigo': 'gestao_status', 'nome': 'Gestão de Serviços - Mudar Status', 'descricao': 'Permite avançar ou retroceder a etapa de um serviço.'},
        {'codigo': 'gestao_fotos', 'nome': 'Gestão de Serviços - Anexar Fotos', 'descricao': 'Permite enviar e excluir fotos técnicas do serviço e dos itens.'},
        {'codigo': 'gestao_financeiro', 'nome': 'Gestão de Serviços - Aba Financeira', 'descricao': 'Visualizar saldos e registrar pagamentos dentro do modal.'},
        {'codigo': 'gestao_cancelar', 'nome': 'Gestão de Serviços - Cancelar Serviço', 'descricao': 'Permite cancelar o serviço.'},
    
        # 4. Linha de Produção (NOVO - MÓDULO INDEPENDENTE, SERÁ REFORMULADO DEPOIS)
        {'codigo': 'producao_operar', 'nome': 'Linha de Produção - Acesso ao Modulo', 'descricao': 'Acesso à tela da linha de produção (Kanban/Listas).'},

        # 5. Financeiro
        {'codigo': 'financeiro_acesso', 'nome': 'Financeiro - Acesso ao Modulo', 'descricao': 'Acesso à tela principal e visualização das contas a pagar/pagas.'},
        {'codigo': 'financeiro_cards', 'nome': 'Financeiro - Cards de Resumo', 'descricao': 'Visualizar os cards de totalizadores no topo da tela.'},
        {'codigo': 'financeiro_criar', 'nome': 'Financeiro - Lançar Despesa', 'descricao': 'Permite criar novas contas e despesas manuais.'},
        {'codigo': 'financeiro_editar', 'nome': 'Financeiro - Editar Lançamento', 'descricao': 'Permite editar valores, datas e descrições de contas existentes.'},
        {'codigo': 'financeiro_pagar', 'nome': 'Financeiro - Dar Baixa (Pagar)', 'descricao': 'Permite clicar no botão de "Confirmar Pagamento" de uma conta.'},
        {'codigo': 'financeiro_excluir', 'nome': 'Financeiro - Excluir Lançamento', 'descricao': 'Permite excluir definitivamente uma conta do sistema.'},
        {'codigo': 'financeiro_fornecedores', 'nome': 'Financeiro - Fornecedores', 'descricao': 'Acesso ao cadastro e gestão de fornecedores.'},

        # 6. Estoque
        {'codigo': 'estoque_gerir', 'nome': 'Controle de Estoque - Acesso ao Modulo', 'descricao': 'Criar produtos, editar preços e movimentar estoque manualmente.'},

        
        # 7. Metas
        {'codigo': 'metas_acesso', 'nome': 'Metas - Acesso ao Modulo', 'descricao': 'Visualizar o atingimento da loja, calendário e ranking da equipe.'},
        {'codigo': 'metas_configurar', 'nome': 'Metas - Configurar Metas', 'descricao': 'Definir os valores mensais, dias úteis e distribuir metas individuais.'},
        
        # 8. RH
        {'codigo': 'rh_acesso', 'nome': 'RH - Acesso ao Modulo', 'descricao': 'Visualizar a lista de funcionários e os dados de contato do perfil.'},
        {'codigo': 'rh_criar', 'nome': 'RH - Cadastrar Funcionário', 'descricao': 'Permite adicionar novos colaboradores ao sistema.'},
        {'codigo': 'rh_editar', 'nome': 'RH - Editar Dados Básicos', 'descricao': 'Permite alterar endereço, telefone, cargo e dados gerais.'},
        {'codigo': 'rh_status', 'nome': 'RH - Demitir / Reativar', 'descricao': 'Permite inativar ou reativar o cadastro de um funcionário.'},
        {'codigo': 'rh_salarios', 'nome': 'RH - Ver e Editar Salários', 'descricao': 'Acesso total aos dados bancários, chave Pix e salário base.'},
        {'codigo': 'rh_documentos', 'nome': 'RH - Gestão de Documentos', 'descricao': 'Fazer upload, baixar e excluir documentos e atestados.'},

        # 9. Relatórios
        {'codigo': 'relatorios_servicos', 'nome': 'Relatórios - Serviços Solicitados', 'descricao': 'Gerar e exportar planilhas de serviços e itens.'},
        {'codigo': 'relatorios_consumo', 'nome': 'Relatórios - Consumo de Materiais', 'descricao': 'Gerar e exportar relatórios de consumo de estoque.'},
        #{'codigo': 'relatorios_financeiro', 'nome': 'Relatórios - Financeiro', 'descricao': 'Gerar relatórios de contas a pagar e fluxo de caixa.'}

        # 10. Usuários de Acesso
        {'codigo': 'acesso_ver', 'nome': 'Usuários de Acesso - Acesso ao Modulo', 'descricao': 'Visualizar a lista de logins de acesso ao sistema.'},
        {'codigo': 'acesso_criar', 'nome': 'Usuários de Acesso - Criar Acesso', 'descricao': 'Permite vincular um colaborador novo a um login e senha.'},
        {'codigo': 'acesso_editar', 'nome': 'Usuários de Acesso - Mudar Senha/Login', 'descricao': 'Permite alterar logins e redefinir senhas de usuários.'},
        {'codigo': 'acesso_status', 'nome': 'Usuários de Acesso - Bloquear/Desbloquear', 'descricao': 'Permite suspender ou liberar o login de um usuário.'},
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