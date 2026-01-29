from src.extensoes import banco_de_dados as db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz # <--- NECESSÁRIO

def hora_brasilia():
    tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(tz)

# Tabela de Associação (Qual Usuário acessa Qual Módulo)
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
    nome = db.Column(db.String(100), nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    senha_hash = db.Column(db.String(256), nullable=False)
    
    # Dados RH
    cpf = db.Column(db.String(14), unique=True, nullable=True)
    telefone = db.Column(db.String(20), nullable=True)
    salario = db.Column(db.Numeric(10, 2), nullable=True)
    
    cargo = db.Column(db.String(20), nullable=False, default='tecnico')
    
    # --- NOVO CAMPO: EQUIPE ---
    # Define a qual time ele pertence (vendas, estoque, etc) para filtros de metas
    equipe = db.Column(db.String(50), default='vendas')
    
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)

    # RELACIONAMENTO: Lista de módulos que este usuário pode acessar
    permissoes = db.relationship('Modulo', secondary=usuario_modulos, lazy='subquery',
        backref=db.backref('usuarios', lazy=True))

    # --- LÓGICA HIERÁRQUICA ---
    NIVEIS_CARGO = {
        'dono': 1,
        'gerente': 2,
        'coordenador': 3,
        'tecnico': 4
    }

    @property
    def nivel_acesso(self):
        """Retorna o número do nível para comparação matemática (Menor é mais poder)"""
        return self.NIVEIS_CARGO.get(self.cargo, 99)
    # ---------------------------------------

    def definir_senha(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def verificar_senha(self, senha):
        return check_password_hash(self.senha_hash, senha)

    def tem_permissao(self, codigo_modulo):
        """
        Verifica se o usuário pode acessar um módulo específico.
        Regra Mestra: O DONO tem acesso a tudo, sempre.
        """
        if self.cargo == 'dono':
            return True
        
        # Verifica se o código do módulo está na lista de permissões do usuário
        for modulo in self.permissoes:
            if modulo.codigo == codigo_modulo:
                return True
        
        return False

    def __repr__(self):
        return f'<Usuario {self.usuario}>'
    
class DocumentoUsuario(db.Model):
    __tablename__ = 'documentos_usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    nome_original = db.Column(db.String(255), nullable=False)
    tipo_arquivo = db.Column(db.String(10), nullable=False)   # ex: 'pdf', 'png'
    tamanho_kb = db.Column(db.Float, nullable=False)
    
    # --- ALTERAÇÃO AQUI ---
    # Substituímos (ou mantemos apenas para referência) o 'nome_arquivo' 
    # por um campo que guarda os bytes reais
    nome_arquivo = db.Column(db.String(255)) # Mantemos para salvar o nome técnico se quiser
    dados_binarios = db.Column(db.LargeBinary) # <--- O ARQUIVO ENTRA AQUI
    # ----------------------

    criado_em = db.Column(db.DateTime, default=hora_brasilia)
    enviado_por_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))

    # Relacionamentos
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id], backref='documentos')
    quem_enviou = db.relationship('Usuario', foreign_keys=[enviado_por_id])    