from src.extensoes import banco_de_dados as db
from datetime import date

class Fornecedor(db.Model):
    __tablename__ = 'fornecedores'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_fantasia = db.Column(db.String(100), nullable=False)
    razao_social = db.Column(db.String(100))
    cnpj = db.Column(db.String(20))     # Para validação e emissão de NFe futura
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    
    # Endereço (Básico)
    cidade = db.Column(db.String(50))
    estado = db.Column(db.String(2))
    
    criado_em = db.Column(db.DateTime, default=db.func.now())
    ativo = db.Column(db.Boolean, default=True)

    # Relacionamento: Um fornecedor tem várias despesas vinculadas
    despesas = db.relationship('Despesa', backref='fornecedor_rel', lazy=True)

    def __repr__(self):
        return f'<Fornecedor {self.nome_fantasia}>'


class Despesa(db.Model):
    __tablename__ = 'despesas'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # --- O BÁSICO ---
    descricao = db.Column(db.String(100), nullable=False)  # Ex: "Conta de Luz", "Salário João"
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    
    # --- CLASSIFICAÇÃO ---
    # Categoria: "Pessoal", "Infraestrutura", "Material", "Impostos", "Financeiro"
    categoria = db.Column(db.String(50), nullable=False)
    
    # Tipo: "fixo" (Aluguel), "variavel" (Comissão/Material)
    tipo_custo = db.Column(db.String(20), nullable=False) 
    
    # --- DATAS (O Coração do Fluxo de Caixa) ---
    data_competencia = db.Column(db.Date, nullable=False) # Mês de referência (Ex: 01/01/2026 para Salário de Janeiro)
    data_vencimento = db.Column(db.Date, nullable=False)  # Dia limite para pagar (Ex: 05/02/2026)
    data_pagamento = db.Column(db.Date)                   # Se preenchido, conta está PAGA.
    
    # --- SITUAÇÃO ---
    status = db.Column(db.String(20), default='pendente') # 'pendente', 'pago', 'atrasado', 'cancelado'
    
    # --- DETALHES DO PAGAMENTO ---
    forma_pagamento = db.Column(db.String(50)) # 'boleto', 'pix', 'dinheiro', 'transferencia', 'cartao_credito'
    codigo_barras = db.Column(db.String(150))  # Para facilitar pagamento
    link_comprovante = db.Column(db.String(255)) # Caminho do arquivo (Upload)
    observacao = db.Column(db.Text)
    
    # --- VÍNCULOS INTELIGENTES (Quem gerou essa despesa?) ---
    
    # 1. Compra de Material (Vincula ao Fornecedor)
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'))
    
    # 2. Salário ou Comissão (Vincula ao Usuário do Sistema)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    usuario = db.relationship('Usuario', backref='despesas_usuario')
    
    # 3. Custo Variável de Venda (Vincula a uma Venda específica - Ex: Comissão, Frete, Material Extra)
    venda_id = db.Column(db.Integer, db.ForeignKey('vendas.id'))
    venda = db.relationship('Venda', backref='custos_atrelados')
    
    criado_em = db.Column(db.DateTime, default=db.func.now())

    @property
    def dias_atraso(self):
        """Calcula dias de atraso se não estiver pago"""
        if self.data_pagamento or self.status == 'cancelado':
            return 0
        hoje = date.today()
        if hoje > self.data_vencimento:
            return (hoje - self.data_vencimento).days
        return 0