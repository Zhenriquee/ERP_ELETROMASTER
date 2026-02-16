from src.extensoes import banco_de_dados as db

# Tabela de Associação: Cargo <-> Módulos (Permissões)
cargo_modulos = db.Table('cargo_modulos',
    db.Column('cargo_id', db.Integer, db.ForeignKey('cargos.id'), primary_key=True),
    db.Column('modulo_id', db.Integer, db.ForeignKey('modulos.id'), primary_key=True)
)

class Setor(db.Model):
    __tablename__ = 'setores'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.String(255))
    ativo = db.Column(db.Boolean, default=True)
    
    cargos = db.relationship('Cargo', backref='setor', lazy=True)

    def __repr__(self):
        return self.nome

class Cargo(db.Model):
    __tablename__ = 'cargos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    setor_id = db.Column(db.Integer, db.ForeignKey('setores.id'), nullable=False)
    
    nivel_hierarquico = db.Column(db.Integer, default=4) 
    descricao = db.Column(db.String(255))
    ativo = db.Column(db.Boolean, default=True)
    
    # Nova relação: Permissões do Cargo
    permissoes = db.relationship('Modulo', secondary=cargo_modulos, lazy='subquery',
        backref=db.backref('cargos', lazy=True))
    
    colaboradores = db.relationship('Colaborador', backref='cargo_ref', lazy=True)

    def __repr__(self):
        return f"{self.nome}"