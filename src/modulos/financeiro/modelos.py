from src.extensoes import banco_de_dados as db
from datetime import date

class Fornecedor(db.Model):
    __tablename__ = 'fornecedores'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_fantasia = db.Column(db.String(100), nullable=False)
    razao_social = db.Column(db.String(100))
    cnpj = db.Column(db.String(20))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    cidade = db.Column(db.String(50))
    estado = db.Column(db.String(2))
    criado_em = db.Column(db.DateTime, default=db.func.now())
    ativo = db.Column(db.Boolean, default=True)
    despesas = db.relationship('Despesa', backref='fornecedor_rel', lazy=True)

    def __repr__(self):
        return f'<Fornecedor {self.nome_fantasia}>'

class Despesa(db.Model):
    __tablename__ = 'despesas'
    
    id = db.Column(db.Integer, primary_key=True)
    
    descricao = db.Column(db.String(100), nullable=False)
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    tipo_custo = db.Column(db.String(20), nullable=False)
    
    data_competencia = db.Column(db.Date, nullable=False)
    data_vencimento = db.Column(db.Date, nullable=False)
    data_pagamento = db.Column(db.Date)
    
    status = db.Column(db.String(20), default='pendente')
    forma_pagamento = db.Column(db.String(50))
    codigo_barras = db.Column(db.String(150))
    link_comprovante = db.Column(db.String(255))
    observacao = db.Column(db.Text)
    
    fornecedor_id = db.Column(db.Integer, db.ForeignKey('fornecedores.id'))
    
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    usuario = db.relationship('Usuario', backref='despesas_usuario')
    
    # --- NOVOS VÍNCULOS PARA O RH ---
    colaborador_id = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=True)
    colaborador = db.relationship('Colaborador', backref='despesas_rh')

    # Identifica se foi criado manualmente ou pelo robô do RH
    # Ex: 'manual', 'rh_automatico'
    origem = db.Column(db.String(30), default='manual') 

    # --- NOVO: VÍNCULO DE PARCELAS ---
    grupo_parcelamento = db.Column(db.String(50), nullable=True)

    venda_id = db.Column(db.Integer, db.ForeignKey('vendas.id'))
    venda = db.relationship('Venda', backref='custos_atrelados')
    
    criado_em = db.Column(db.DateTime, default=db.func.now())

    @property
    def dias_atraso(self):
        if self.data_pagamento or self.status == 'cancelado':
            return 0
        hoje = date.today()
        if hoje > self.data_vencimento:
            return (hoje - self.data_vencimento).days
        return 0
    
    @property
    def parcelamento_info(self):
        """Calcula dinamicamente ' - Parc. 1/3' lendo do banco de dados na hora de exibir"""
        if self.grupo_parcelamento:
            parcelas = Despesa.query.filter_by(grupo_parcelamento=self.grupo_parcelamento).order_by(Despesa.data_vencimento.asc(), Despesa.id.asc()).all()
            total = len(parcelas)
            if total > 1:
                try:
                    indice = parcelas.index(self) + 1
                    return f" - Parc. {indice}/{total}"
                except ValueError:
                    return ""
        return ""