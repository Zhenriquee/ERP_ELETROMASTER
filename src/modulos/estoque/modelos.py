from src.extensoes import banco_de_dados as db
from datetime import datetime

class ProdutoEstoque(db.Model):
    __tablename__ = 'produtos_estoque'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    
    # NOVAS REGRAS DE UNIDADE
    # Apenas Gramas (G) ou Quilogramas (KG)
    unidade = db.Column(db.String(5), default='KG') 
    
    quantidade_atual = db.Column(db.Numeric(10, 3), default=0.0)
    quantidade_minima = db.Column(db.Numeric(10, 3), default=5.0)
    valor_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    
    # FATORES DE CONSUMO (Para cálculo automático na produção)
    # Ex: 0.200 (200g ou 0.2kg) por m2
    consumo_por_m2 = db.Column(db.Numeric(10, 4), default=0.0) 
    consumo_por_m3 = db.Column(db.Numeric(10, 4), default=0.0)
    
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    movimentacoes = db.relationship('MovimentacaoEstoque', backref='produto', lazy=True)

    def __repr__(self):
        return f'<Produto {self.nome}>'

class MovimentacaoEstoque(db.Model):
    __tablename__ = 'movimentacoes_estoque'
    
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produtos_estoque.id'), nullable=False)
    
    tipo = db.Column(db.String(20), nullable=False) # entrada, saida, ajuste
    quantidade = db.Column(db.Numeric(10, 3), nullable=False)
    
    saldo_anterior = db.Column(db.Numeric(10, 3))
    saldo_novo = db.Column(db.Numeric(10, 3))
    
    data_movimentacao = db.Column(db.DateTime, default=datetime.now)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    usuario = db.relationship('Usuario', backref='movimentacoes')
    
    origem = db.Column(db.String(50)) # venda, compra, ajuste_manual, producao
    referencia_id = db.Column(db.Integer) # ID da venda ou ordem de serviço
    observacao = db.Column(db.String(255))