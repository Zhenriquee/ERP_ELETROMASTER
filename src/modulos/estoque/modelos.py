from src.extensoes import banco_de_dados as db
from datetime import datetime

class ProdutoEstoque(db.Model):
    __tablename__ = 'produtos_estoque'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    unidade = db.Column(db.String(10), default='KG')
    
    quantidade_atual = db.Column(db.Numeric(10, 3), default=0.000)
    quantidade_minima = db.Column(db.Numeric(10, 3), default=5.000)
    
    # --- PREÇOS DE VENDA ---
    preco_m2 = db.Column(db.Numeric(10, 2), nullable=True, default=0.00)
    preco_m3 = db.Column(db.Numeric(10, 2), nullable=True, default=0.00)
    
    # --- FICHA TÉCNICA (AGORA COM 3 CASAS DECIMAIS) ---
    consumo_por_m2 = db.Column(db.Numeric(10, 3), nullable=True, default=0.000)
    consumo_por_m3 = db.Column(db.Numeric(10, 3), nullable=True, default=0.000)
    
    ativo = db.Column(db.Boolean, default=True)
    movimentacoes = db.relationship('MovimentacaoEstoque', backref='produto', lazy=True)

class MovimentacaoEstoque(db.Model):
    __tablename__ = 'movimentacoes_estoque'
    
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos_estoque.id'), nullable=False)
    
    tipo = db.Column(db.String(20), nullable=False) 
    quantidade = db.Column(db.Numeric(10, 3), nullable=False)
    saldo_anterior = db.Column(db.Numeric(10, 3))
    saldo_novo = db.Column(db.Numeric(10, 3))
    
    origem = db.Column(db.String(50))
    referencia_id = db.Column(db.Integer) 
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    data_movimentacao = db.Column(db.DateTime, default=datetime.utcnow)
    observacao = db.Column(db.String(255))
    
    usuario = db.relationship('Usuario')