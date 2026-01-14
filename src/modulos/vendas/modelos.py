from src.extensoes import banco_de_dados as db
from datetime import datetime
from flask_login import current_user

class CorServico(db.Model):
    __tablename__ = 'cores_servico'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    unidade_medida = db.Column(db.String(5), nullable=False) # 'm2' ou 'm3'
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    historico = db.relationship('HistoricoPrecoCor', backref='cor', lazy=True)

class HistoricoPrecoCor(db.Model):
    __tablename__ = 'historico_precos_cor'
    id = db.Column(db.Integer, primary_key=True)
    cor_id = db.Column(db.Integer, db.ForeignKey('cores_servico.id'), nullable=False)
    preco_anterior = db.Column(db.Numeric(10, 2), nullable=False)
    preco_novo = db.Column(db.Numeric(10, 2), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_alteracao = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.relationship('Usuario')

class Venda(db.Model):
    __tablename__ = 'vendas'
    id = db.Column(db.Integer, primary_key=True)
    
    # 1. Cliente
    tipo_cliente = db.Column(db.String(2), nullable=False) # 'PF' ou 'PJ'
    
    # Campos mapeados:
    # Se PF: cliente_nome = Nome, cliente_documento = CPF
    # Se PJ: cliente_nome = Nome Fantasia, cliente_documento = CNPJ
    cliente_nome = db.Column(db.String(150), nullable=False)
    cliente_solicitante = db.Column(db.String(100), nullable=True) # Exclusivo PJ (Nome de quem pediu)
    cliente_documento = db.Column(db.String(20), nullable=True)
    
    # Contato e Endereço (Comuns)
    cliente_contato = db.Column(db.String(50), nullable=False) # Telefone
    cliente_email = db.Column(db.String(100), nullable=True)
    cliente_endereco = db.Column(db.String(255), nullable=True) # <--- Novo Campo

    # 2. Serviço
    descricao_servico = db.Column(db.Text, nullable=False)
    observacoes_internas = db.Column(db.Text, nullable=True)
    
    # 3. Metragem e Cor
    tipo_medida = db.Column(db.String(5), nullable=False)
    dimensao_1 = db.Column(db.Numeric(10, 2), nullable=False)
    dimensao_2 = db.Column(db.Numeric(10, 2), nullable=False)
    dimensao_3 = db.Column(db.Numeric(10, 2), nullable=True)
    metragem_total = db.Column(db.Numeric(10, 2), nullable=False)
    quantidade_pecas = db.Column(db.Integer, default=1)
    
    cor_id = db.Column(db.Integer, db.ForeignKey('cores_servico.id'), nullable=False)
    cor_nome_snapshot = db.Column(db.String(100))
    preco_unitario_snapshot = db.Column(db.Numeric(10, 2))
    
    # 4. Financeiro
    valor_acrescimo = db.Column(db.Numeric(10, 2), default=0.00)
    valor_base = db.Column(db.Numeric(10, 2), nullable=False)
    tipo_desconto = db.Column(db.String(10), nullable=True)
    valor_desconto_aplicado = db.Column(db.Numeric(10, 2), default=0.00)
    valor_final = db.Column(db.Numeric(10, 2), nullable=False)
    
    status = db.Column(db.String(20), default='orcamento')
    vendedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    vendedor = db.relationship('Usuario')
    cor = db.relationship('CorServico')