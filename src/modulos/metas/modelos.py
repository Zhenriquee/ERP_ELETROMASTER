from src.extensoes import banco_de_dados as db
from datetime import datetime

class MetaMensal(db.Model):
    __tablename__ = 'metas_mensais'
    
    id = db.Column(db.Integer, primary_key=True)
    mes = db.Column(db.Integer, nullable=False)
    ano = db.Column(db.Integer, nullable=False)
    
    valor_loja = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Campo calculado (mantido para facilitar contas rápidas)
    dias_uteis = db.Column(db.Integer, nullable=False)
    
    # NOVOS CAMPOS PARA O CALENDÁRIO
    # Armazena indices dos dias: 0=Seg, 1=Ter... 6=Dom. Ex: "0,1,2,3,4,5" (Seg a Sab)
    config_semana = db.Column(db.String(20), default="0,1,2,3,4") 
    
    # Armazena dias específicos do mês que não haverá trabalho. Ex: "12,25" (Dia 12 e 25)
    config_feriados = db.Column(db.String(100), default="")

    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    criado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    metas_vendedores = db.relationship('MetaVendedor', backref='meta_mensal', cascade="all, delete-orphan")

class MetaVendedor(db.Model):
    __tablename__ = 'metas_vendedores'
    
    id = db.Column(db.Integer, primary_key=True)
    meta_mensal_id = db.Column(db.Integer, db.ForeignKey('metas_mensais.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    valor_meta = db.Column(db.Numeric(10, 2), nullable=False) # Ex: 25.000,00
    
    # Relacionamento para acessar dados do usuário (nome, etc)
    usuario = db.relationship('Usuario')