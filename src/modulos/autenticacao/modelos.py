from src.extensoes import banco_de_dados as db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz

def hora_brasilia():
    tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(tz)

# Tabela de Associação (Permissões Manuais/Extras específicas de um usuário)
# Útil se você quiser dar uma permissão a alguém sem dar ao cargo todo
usuario_modulos = db.Table('usuario_modulos',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuarios.id'), primary_key=True),
    db.Column('modulo_id', db.Integer, db.ForeignKey('modulos.id'), primary_key=True)
)

class Modulo(db.Model):
    __tablename__ = 'modulos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    descricao = db.Column(db.String(255), nullable=True) # <--- NOVA LINHA AQUI
    
    def __repr__(self):
        return f'<Modulo {self.nome}>'

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    
    # Vínculo Obrigatório com o Colaborador (RH)
    colaborador_id = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), unique=True, nullable=False)
    
    # Dados de Acesso
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento de permissões EXTRAS (além das do cargo)
    permissoes = db.relationship('Modulo', secondary=usuario_modulos, lazy='subquery',
        backref=db.backref('usuarios', lazy=True))

    # =================================================================
    # --- PROPRIEDADES DINÂMICAS (Buscam dados do RH / Corporativo) ---
    # =================================================================
    
    @property
    def nome(self):
        """Retorna o nome completo do funcionário"""
        if self.colaborador:
            return self.colaborador.nome_completo
        return self.usuario

    @property
    def cargo(self):
        """Retorna o nome do Cargo vindo do RH"""
        if self.colaborador and self.colaborador.cargo_ref:
            return self.colaborador.cargo_ref.nome
        return 'Sem Cargo'

    @property
    def equipe(self):
        """Retorna o Setor do colaborador como 'equipe'"""
        if self.colaborador and self.colaborador.cargo_ref:
            return self.colaborador.cargo_ref.setor.nome
        return 'Geral'

    @property
    def nivel_acesso(self):
        """Retorna o nível hierárquico (1=Dono ... 4=Operacional)"""
        if self.colaborador and self.colaborador.cargo_ref:
            return self.colaborador.cargo_ref.nivel_hierarquico
        
        # Fallback de segurança caso algo falhe
        if self.cargo and self.cargo.lower() == 'dono':
            return 1
        return 99

    # =================================================================
    # --- SEGURANÇA E LOGIN ---
    # =================================================================

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def tem_permissao(self, codigo_modulo):
        """
        Verifica se o usuário pode acessar um módulo.
        Ordem de Checagem:
        1. É Dono? (Acesso Total)
        2. O Cargo dele tem a permissão? (Herdado do Corporativo)
        3. Ele tem uma permissão manual extra?
        """
        # 1. Acesso Total (Dono ou Nível 1)
        if self.nivel_acesso <= 1:
            return True
        
        cargo_nome = self.cargo.lower() if self.cargo else ''
        if cargo_nome == 'dono':
            return True
            
        # 2. Verifica Permissões do CARGO (Padrão)
        if self.colaborador and self.colaborador.cargo_ref:
            # Itera sobre os módulos vinculados ao Cargo
            for mod in self.colaborador.cargo_ref.permissoes:
                if mod.codigo == codigo_modulo:
                    return True

        # 3. Verifica Permissões MANUAIS (Exceções)
        for mod in self.permissoes:
            if mod.codigo == codigo_modulo:
                return True
        
        return False

    def __repr__(self):
        return f'<Usuario {self.usuario}>'