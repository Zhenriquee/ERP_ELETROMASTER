from src.extensoes import banco_de_dados as db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    senha_hash = db.Column(db.String(256), nullable=False)
    
    # Novos Campos de RH
    cpf = db.Column(db.String(14), unique=True, nullable=True) # Formato 000.000.000-00
    telefone = db.Column(db.String(20), nullable=True)
    salario = db.Column(db.Numeric(10, 2), nullable=True) # Ex: 1500.00 (Numeric é melhor para dinheiro)
    
    cargo = db.Column(db.String(20), nullable=False, default='tecnico')
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Hierarquia Invertida (1 é o mais alto)
    NIVEIS_CARGO = {
        'dono': 1,
        'gerente': 2,
        'coordenador': 3,
        'tecnico': 4
    }

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    @property
    def nivel_acesso(self):
        return self.NIVEIS_CARGO.get(self.cargo, 99)

    def tem_permissao(self, cargo_minimo_necessario):
        """
        Verifica hierarquia.
        Agora a lógica é INVERTIDA: Nível menor = Mais poder.
        Ex: Se exijo 'gerente' (2), o 'dono' (1) passa (1 <= 2).
        """
        nivel_necessario = self.NIVEIS_CARGO.get(cargo_minimo_necessario, 0)
        return self.nivel_acesso <= nivel_necessario

    def __repr__(self):
        return f'<Usuario {self.usuario}>'