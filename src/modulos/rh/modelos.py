from src.extensoes import banco_de_dados as db
from datetime import datetime
import pytz

def hora_brasilia():
    tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(tz)

class Colaborador(db.Model):
    __tablename__ = 'colaboradores'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_completo = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    rg = db.Column(db.String(20))
    data_nascimento = db.Column(db.Date)
    
    email_pessoal = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    endereco = db.Column(db.String(255))
    
    cargo_id = db.Column(db.Integer, db.ForeignKey('cargos.id'), nullable=False)
    data_admissao = db.Column(db.Date, nullable=False)
    tipo_contrato = db.Column(db.String(20))
    
    # --- DADOS FINANCEIROS ---
    salario_base = db.Column(db.Numeric(10, 2))

    # --- NOVO CAMPO: Define se o colaborador recebe meta ---
    faz_parte_meta = db.Column(db.Boolean, default=False)
    
    # Estes campos estavam faltando:
    chave_pix = db.Column(db.String(100))
    banco = db.Column(db.String(50))
    agencia = db.Column(db.String(20))
    conta = db.Column(db.String(20))
    
    frequencia_pagamento = db.Column(db.String(20), default='mensal')
    dia_pagamento = db.Column(db.String(20)) # Ex: "5" ou "15,30" ou "4" (Sexta)
    
    percentual_adiantamento = db.Column(db.Integer, default=40)
    # -------------------------
    
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    usuario_acesso = db.relationship('Usuario', backref='colaborador', uselist=False)
    
    documentos = db.relationship('DocumentoColaborador', backref='colaborador', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return self.nome_completo

class DocumentoColaborador(db.Model):
    __tablename__ = 'documentos_colaboradores'
    
    id = db.Column(db.Integer, primary_key=True)
    colaborador_id = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), nullable=False)
    
    nome_original = db.Column(db.String(255), nullable=False)
    tipo_arquivo = db.Column(db.String(10), nullable=False)
    tamanho_kb = db.Column(db.Float, nullable=False)
    nome_arquivo = db.Column(db.String(255))
    dados_binarios = db.Column(db.LargeBinary)
    descricao = db.Column(db.String(100))

    criado_em = db.Column(db.DateTime, default=hora_brasilia)
    enviado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    quem_enviou = db.relationship('Usuario', foreign_keys=[enviado_por_id])