from src.extensoes import banco_de_dados as db
from datetime import datetime

class Colaborador(db.Model):
    __tablename__ = 'colaboradores'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Dados Pessoais
    nome_completo = db.Column(db.String(150), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    rg = db.Column(db.String(20))
    data_nascimento = db.Column(db.Date)
    
    # Contato
    email_pessoal = db.Column(db.String(100))
    telefone = db.Column(db.String(20))
    endereco = db.Column(db.String(255))
    
    # Dados Contratuais
    cargo_id = db.Column(db.Integer, db.ForeignKey('cargos.id'), nullable=False)
    data_admissao = db.Column(db.Date, nullable=False)
    tipo_contrato = db.Column(db.String(20)) # CLT, PJ, Estágio
    salario_base = db.Column(db.Numeric(10, 2))
    
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento One-to-One com Usuario (Um colaborador tem 0 ou 1 usuário)
    usuario_acesso = db.relationship('Usuario', backref='colaborador', uselist=False)

    def __repr__(self):
        return self.nome_completo