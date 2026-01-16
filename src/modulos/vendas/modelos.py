from src.extensoes import banco_de_dados as db
from datetime import datetime
from flask_login import current_user
import pytz

def hora_brasilia():
    tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(tz)

class CorServico(db.Model):
    __tablename__ = 'cores_servico'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    unidade_medida = db.Column(db.String(5), nullable=False)
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

class Pagamento(db.Model):
    __tablename__ = 'pagamentos'
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('vendas.id'), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    data_pagamento = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(20)) 
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    usuario = db.relationship('Usuario')

# --- NOVO MODELO: ITENS DA VENDA ---
class ItemVenda(db.Model):
    __tablename__ = 'venda_itens'
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('vendas.id'), nullable=False)
    
    descricao = db.Column(db.String(200), nullable=False)
    cor_id = db.Column(db.Integer, db.ForeignKey('cores_servico.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)
    
    # --- NOVOS CAMPOS DE CONTROLE POR ITEM ---
    status = db.Column(db.String(20), default='pendente') # pendente, producao, pronto, entregue
    
    data_inicio_producao = db.Column(db.DateTime, nullable=True)
    data_pronto = db.Column(db.DateTime, nullable=True)
    data_entregue = db.Column(db.DateTime, nullable=True)
    
    cor = db.relationship('CorServico')

class Venda(db.Model):
    __tablename__ = 'vendas'
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificador do Modo de Venda
    modo = db.Column(db.String(20), default='simples') # 'simples' ou 'multipla'

    # 1. Cliente
    tipo_cliente = db.Column(db.String(2), nullable=False)
    cliente_nome = db.Column(db.String(150), nullable=False)
    cliente_solicitante = db.Column(db.String(100), nullable=True)
    cliente_documento = db.Column(db.String(20), nullable=True)
    cliente_contato = db.Column(db.String(50), nullable=False)
    cliente_email = db.Column(db.String(100), nullable=True)
    cliente_endereco = db.Column(db.String(255), nullable=True)

    # 2. Campos Venda Simples (Tornam-se Opcionais/Nullable no banco se for multipla)
    descricao_servico = db.Column(db.Text, nullable=True) 
    observacoes_internas = db.Column(db.Text, nullable=True)
    tipo_medida = db.Column(db.String(5), nullable=True)
    dimensao_1 = db.Column(db.Numeric(10, 2), nullable=True)
    dimensao_2 = db.Column(db.Numeric(10, 2), nullable=True)
    dimensao_3 = db.Column(db.Numeric(10, 2), nullable=True)
    metragem_total = db.Column(db.Numeric(10, 2), nullable=True)
    quantidade_pecas = db.Column(db.Integer, default=1)
    cor_id = db.Column(db.Integer, db.ForeignKey('cores_servico.id'), nullable=True)
    cor_nome_snapshot = db.Column(db.String(100), nullable=True)
    preco_unitario_snapshot = db.Column(db.Numeric(10, 2), nullable=True)
    
    # 3. Financeiro
    valor_base = db.Column(db.Numeric(10, 2), nullable=False) # Soma dos itens
    valor_acrescimo = db.Column(db.Numeric(10, 2), default=0.00)
    tipo_desconto = db.Column(db.String(10), nullable=True)
    valor_desconto_aplicado = db.Column(db.Numeric(10, 2), default=0.00)
    valor_final = db.Column(db.Numeric(10, 2), nullable=False)
    
    # 4. Status e Controle
    status = db.Column(db.String(20), default='orcamento')
    status_pagamento = db.Column(db.String(20), default='pendente')
    vendedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Cancelamento
    motivo_cancelamento = db.Column(db.Text, nullable=True)
    data_cancelamento = db.Column(db.DateTime, nullable=True)
    usuario_cancelamento_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)

    # Relacionamentos
    vendedor = db.relationship('Usuario', foreign_keys=[vendedor_id])
    cor = db.relationship('CorServico') # Apenas para venda simples
    pagamentos = db.relationship('Pagamento', backref='venda', lazy=True)
    usuario_cancelamento = db.relationship('Usuario', foreign_keys=[usuario_cancelamento_id])
    
    # Auditoria
    data_inicio_producao = db.Column(db.DateTime, nullable=True)
    usuario_producao_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    usuario_producao = db.relationship('Usuario', foreign_keys=[usuario_producao_id])
    
    data_pronto = db.Column(db.DateTime, nullable=True)
    usuario_pronto_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    usuario_pronto = db.relationship('Usuario', foreign_keys=[usuario_pronto_id])
    
    data_entrega = db.Column(db.DateTime, nullable=True)
    usuario_entrega_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    usuario_entrega = db.relationship('Usuario', foreign_keys=[usuario_entrega_id])

    # NOVO RELACIONAMENTO DE ITENS
    itens = db.relationship('ItemVenda', backref='venda', lazy=True, cascade="all, delete-orphan")

    @property
    def total_pago(self):
        return sum(p.valor for p in self.pagamentos)

    @property
    def valor_restante(self):
        return self.valor_final - self.total_pago