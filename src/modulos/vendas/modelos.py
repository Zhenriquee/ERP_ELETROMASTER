from src.extensoes import banco_de_dados as db
from datetime import datetime
import pytz

def hora_brasilia():
    tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(tz)

# --- MODELOS AUXILIARES ---
class CorServico(db.Model):
    __tablename__ = 'cores_servico'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    preco_m2 = db.Column(db.Numeric(10, 2), nullable=True)
    preco_m3 = db.Column(db.Numeric(10, 2), nullable=True)
    ativo = db.Column(db.Boolean, default=True)
    historico = db.relationship('HistoricoPrecoCor', backref='cor', lazy=True)

class HistoricoPrecoCor(db.Model):
    __tablename__ = 'historico_precos_cor'
    id = db.Column(db.Integer, primary_key=True)
    cor_id = db.Column(db.Integer, db.ForeignKey('cores_servico.id'), nullable=False)
    preco_m2_anterior = db.Column(db.Numeric(10, 2))
    preco_m2_novo = db.Column(db.Numeric(10, 2))
    preco_m3_anterior = db.Column(db.Numeric(10, 2))
    preco_m3_novo = db.Column(db.Numeric(10, 2))
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

# --- ITEM DA VENDA (ATUALIZADO) ---
class ItemVenda(db.Model):
    __tablename__ = 'venda_itens'
    id = db.Column(db.Integer, primary_key=True)
    venda_id = db.Column(db.Integer, db.ForeignKey('vendas.id'), nullable=False)
    
    descricao = db.Column(db.String(200), nullable=False)
    
    # Vínculos de Produto
    cor_id = db.Column(db.Integer, db.ForeignKey('cores_servico.id'), nullable=True) # Legado
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos_estoque.id'), nullable=True) # Novo
    
    # Valores Financeiros
    quantidade = db.Column(db.Integer, nullable=False)
    valor_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)
    
    # --- NOVOS CAMPOS PARA CÁLCULO DE CONSUMO ---
    # Armazena a área/volume total deste item para calcular a baixa de tinta depois
    metragem_total = db.Column(db.Numeric(10, 3), default=0.0) 
    tipo_medida = db.Column(db.String(5), default='m2') # m2 ou m3
    
    status = db.Column(db.String(20), default='pendente')
    
    # --- CAMPOS DE RASTREIO DE PRODUÇÃO (MANTIDOS) ---
    data_inicio_producao = db.Column(db.DateTime, nullable=True)
    usuario_producao_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    data_pronto = db.Column(db.DateTime, nullable=True)
    usuario_pronto_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    data_entregue = db.Column(db.DateTime, nullable=True)
    usuario_entrega_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    
    # Relacionamentos
    cor = db.relationship('CorServico')
    produto = db.relationship('ProdutoEstoque')
    
    usuario_producao = db.relationship('Usuario', foreign_keys=[usuario_producao_id])
    usuario_pronto = db.relationship('Usuario', foreign_keys=[usuario_pronto_id])
    usuario_entrega = db.relationship('Usuario', foreign_keys=[usuario_entrega_id])
    
    # Relacionamento com as Fotos
    fotos = db.relationship('FotoItemVenda', backref='item', cascade='all, delete-orphan')

# --- VENDA PAI (MANTIDO) ---
class Venda(db.Model):
    __tablename__ = 'vendas'
    id = db.Column(db.Integer, primary_key=True)
    
    modo = db.Column(db.String(20), default='simples')

    # Cliente
    tipo_cliente = db.Column(db.String(2), nullable=False)
    cliente_nome = db.Column(db.String(150), nullable=False)
    cliente_solicitante = db.Column(db.String(100), nullable=True)
    cliente_documento = db.Column(db.String(20), nullable=True)
    cliente_contato = db.Column(db.String(50), nullable=False)
    cliente_email = db.Column(db.String(100), nullable=True)
    cliente_endereco = db.Column(db.String(255), nullable=True)

    # Detalhes (Venda Simples)
    descricao_servico = db.Column(db.Text, nullable=True) 
    observacoes_internas = db.Column(db.Text, nullable=True)
    tipo_medida = db.Column(db.String(5), nullable=True)
    dimensao_1 = db.Column(db.Numeric(10, 2), nullable=True)
    dimensao_2 = db.Column(db.Numeric(10, 2), nullable=True)
    dimensao_3 = db.Column(db.Numeric(10, 2), nullable=True)
    metragem_total = db.Column(db.Numeric(10, 2), nullable=True)
    quantidade_pecas = db.Column(db.Integer, default=1)
    
    cor_id = db.Column(db.Integer, db.ForeignKey('cores_servico.id'), nullable=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos_estoque.id'), nullable=True)
    
    cor_nome_snapshot = db.Column(db.String(100), nullable=True)
    preco_unitario_snapshot = db.Column(db.Numeric(10, 2), nullable=True)
    
    # Financeiro
    valor_base = db.Column(db.Numeric(10, 2), nullable=False)
    valor_acrescimo = db.Column(db.Numeric(10, 2), default=0.00)
    tipo_desconto = db.Column(db.String(10), nullable=True)
    valor_desconto_aplicado = db.Column(db.Numeric(10, 2), default=0.00)
    valor_final = db.Column(db.Numeric(10, 2), nullable=False)
    
    status = db.Column(db.String(20), default='orcamento')
    status_pagamento = db.Column(db.String(20), default='pendente')
    vendedor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    criado_em = db.Column(db.DateTime, default=hora_brasilia)
    
    # Cancelamento
    motivo_cancelamento = db.Column(db.Text, nullable=True)
    data_cancelamento = db.Column(db.DateTime, nullable=True)
    usuario_cancelamento_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)

    # Relacionamentos
    vendedor = db.relationship('Usuario', foreign_keys=[vendedor_id])
    cor = db.relationship('CorServico') 
    produto = db.relationship('ProdutoEstoque')
    
    pagamentos = db.relationship('Pagamento', backref='venda', lazy=True)
    usuario_cancelamento = db.relationship('Usuario', foreign_keys=[usuario_cancelamento_id])
    
    # Auditoria de Status da Venda (Quando avança em bloco)
    data_inicio_producao = db.Column(db.DateTime, nullable=True)
    usuario_producao_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    usuario_producao = db.relationship('Usuario', foreign_keys=[usuario_producao_id])
    
    data_pronto = db.Column(db.DateTime, nullable=True)
    usuario_pronto_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    usuario_pronto = db.relationship('Usuario', foreign_keys=[usuario_pronto_id])
    
    data_entrega = db.Column(db.DateTime, nullable=True)
    usuario_entrega_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    usuario_entrega = db.relationship('Usuario', foreign_keys=[usuario_entrega_id])

    itens = db.relationship('ItemVenda', backref='venda', lazy=True, cascade="all, delete-orphan")
    prioridade = db.Column(db.Boolean, default=False)

    @property
    def valor_pago(self):
        if not self.pagamentos: return 0.0
        return sum(p.valor for p in self.pagamentos)

    @property
    def valor_restante(self):
        pago = self.valor_pago
        restante = float(self.valor_final) - float(pago)
        return max(0.0, restante)

class ItemVendaHistorico(db.Model):
    __tablename__ = 'item_venda_historico'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('venda_itens.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    status_anterior = db.Column(db.String(20), nullable=False)
    status_novo = db.Column(db.String(20), nullable=False)
    acao = db.Column(db.String(50))
    
    data_acao = db.Column(db.DateTime, default=hora_brasilia)
    
    usuario = db.relationship('Usuario')
    item = db.relationship('ItemVenda', backref=db.backref('historico_acoes', lazy=True, cascade="all, delete-orphan"))

# --- TABELA DE FOTOS (ALTERADA PARA BINÁRIO) ---
class FotoItemVenda(db.Model):
    __tablename__ = 'fotos_itens_venda'
    
    id = db.Column(db.Integer, primary_key=True)
    item_venda_id = db.Column(db.Integer, db.ForeignKey('venda_itens.id'), nullable=False)
    
    # NOVAS COLUNAS PARA ARMAZENAMENTO NO BANCO
    nome_arquivo = db.Column(db.String(255), nullable=False) # Ex: "foto1.jpg"
    tipo_mime = db.Column(db.String(50), nullable=False)     # Ex: "image/jpeg"
    dados_binarios = db.Column(db.LargeBinary, nullable=False) # O arquivo em si (BLOB)
    
    # REMOVIDO: caminho_arquivo
    
    # 'recebimento' (antes) ou 'entrega' (depois) ou 'gestao'
    etapa = db.Column(db.String(20), nullable=False) 
    
    data_upload = db.Column(db.DateTime, default=hora_brasilia)
    enviado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    
    usuario = db.relationship('Usuario')    