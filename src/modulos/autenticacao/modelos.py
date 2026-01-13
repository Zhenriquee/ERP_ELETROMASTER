from src.extensoes import banco_de_dados as db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False) # Nome completo (Ex: João da Silva)
    
    # NOVO CAMPO DE LOGIN
    usuario = db.Column(db.String(50), unique=True, nullable=False) # Login (Ex: joao.silva)
    
    # Email agora é opcional (nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True) 
    
    senha_hash = db.Column(db.String(256), nullable=False)
    cargo = db.Column(db.String(20), nullable=False, default='tecnico')
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    NIVEIS_CARGO = {
        'tecnico': 1,
        'coordenador': 2,
        'gerente': 3,
        'dono': 4
    }

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def tem_permissao(self, cargo_minimo_necessario):
        nivel_usuario = self.NIVEIS_CARGO.get(self.cargo, 0)
        nivel_necessario = self.NIVEIS_CARGO.get(cargo_minimo_necessario, 99)
        return nivel_usuario >= nivel_necessario

    def __repr__(self):
        return f'<Usuario {self.usuario}>'