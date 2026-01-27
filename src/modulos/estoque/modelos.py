from src.extensoes import banco_de_dados as db
from datetime import datetime

class ProdutoEstoque(db.Model):
    __tablename__ = 'produtos_estoque'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    unidade = db.Column(db.String(10), default='CX') # CX, UN, LT, KG
    
    # Quantidade atual (Numeric 10,3 permite ex: 150.333)
    quantidade_atual = db.Column(db.Numeric(10, 3), default=0.000)
    estoque_minimo = db.Column(db.Numeric(10, 3), default=5.000)
    
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamento com movimentações
    movimentacoes = db.relationship('MovimentacaoEstoque', backref='produto', lazy=True)

class MovimentacaoEstoque(db.Model):
    __tablename__ = 'movimentacoes_estoque'
    
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos_estoque.id'), nullable=False)
    
    tipo = db.Column(db.String(10), nullable=False) # 'entrada' ou 'saida'
    quantidade = db.Column(db.Numeric(10, 3), nullable=False)
    saldo_anterior = db.Column(db.Numeric(10, 3))
    saldo_novo = db.Column(db.Numeric(10, 3))
    
    origem = db.Column(db.String(20)) # 'manual', 'compra', 'producao'
    referencia_id = db.Column(db.Integer) # ID da Despesa ou do ItemVenda
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    data = db.Column(db.DateTime, default=datetime.utcnow)
    observacao = db.Column(db.String(255))
    
    usuario = db.relationship('Usuario')