from src.extensoes import banco_de_dados as db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz

def hora_brasilia():
    tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(tz)

# Tabela de Associação (Permissões Manuais/Extras)
usuario_modulos = db.Table('usuario_modulos',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuarios.id'), primary_key=True),
    db.Column('modulo_id', db.Integer, db.ForeignKey('modulos.id'), primary_key=True)
)

class Modulo(db.Model):
    __tablename__ = 'modulos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)
    codigo = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Modulo {self.nome}>'

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    
    # --- VÍNCULO COM O RH (A Mudança Principal) ---
    colaborador_id = db.Column(db.Integer, db.ForeignKey('colaboradores.id'), unique=True, nullable=False)
    
    # Dados de Acesso
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    senha_hash = db.Column(db.String(256), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True) # E-mail de recuperação
    
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento de permissões extras
    permissoes = db.relationship('Modulo', secondary=usuario_modulos, lazy='subquery',
        backref=db.backref('usuarios', lazy=True))

    # =================================================================
    # --- PROPRIEDADES DINÂMICAS (Buscam dados do Colaborador) ---
    # =================================================================
    
    @property
    def nome(self):
        """Retorna o nome completo do funcionário ou o login se der erro"""
        if self.colaborador:
            return self.colaborador.nome_completo
        return self.usuario

    @property
    def cargo(self):
        """Retorna o nome do Cargo (Ex: Dono, Vendedor) vindo do RH"""
        if self.colaborador and self.colaborador.cargo_ref:
            return self.colaborador.cargo_ref.nome
        return 'Sem Cargo'

    @property
    def equipe(self):
        """Retorna o Setor como 'equipe' para compatibilidade"""
        if self.colaborador and self.colaborador.cargo_ref:
            return self.colaborador.cargo_ref.setor.nome
        return 'Geral'

    @property
    def nivel_acesso(self):
        """Retorna o nível numérico (1=Dono ... 4=Operacional)"""
        if self.colaborador and self.colaborador.cargo_ref:
            return self.colaborador.cargo_ref.nivel_hierarquico
        # Fallback de segurança
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
        1. Se for DONO (Nível 1), libera tudo.
        2. Se não, verifica as permissões manuais.
        """
        # Verifica Cargo (Case Insensitive)
        cargo_atual = self.cargo.lower() if self.cargo else ''
        
        if cargo_atual == 'dono':
            return True
            
        # Verifica Nível Hierárquico (1 = Dono/Diretor)
        if self.nivel_acesso <= 1:
            return True
        
        # Verifica Permissões Específicas
        for modulo in self.permissoes:
            if modulo.codigo == codigo_modulo:
                return True
        
        return False

    def __repr__(self):
        return f'<Usuario {self.usuario}>'

# Classe DocumentoUsuario (Mantida para uploads)
class DocumentoUsuario(db.Model):
    __tablename__ = 'documentos_usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    nome_original = db.Column(db.String(255), nullable=False)
    tipo_arquivo = db.Column(db.String(10), nullable=False)
    tamanho_kb = db.Column(db.Float, nullable=False)
    nome_arquivo = db.Column(db.String(255))
    dados_binarios = db.Column(db.LargeBinary)

    criado_em = db.Column(db.DateTime, default=hora_brasilia)
    enviado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    usuario = db.relationship('Usuario', foreign_keys=[usuario_id], backref='documentos')
    quem_enviou = db.relationship('Usuario', foreign_keys=[enviado_por_id])