from src.extensoes import banco_de_dados as db

class Setor(db.Model):
    __tablename__ = 'setores'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.String(255))
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamento com Cargo
    cargos = db.relationship('Cargo', backref='setor', lazy=True)

    def __repr__(self):
        return self.nome

class Cargo(db.Model):
    __tablename__ = 'cargos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    setor_id = db.Column(db.Integer, db.ForeignKey('setores.id'), nullable=False)
    
    # Nível hierárquico (1=Dono, 2=Gerente, 3=Coord, 4=Operacional)
    # Isso ajuda a filtrar quem pode ver o que no sistema futuramente
    nivel_hierarquico = db.Column(db.Integer, default=4) 
    
    descricao = db.Column(db.String(255))
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamento com Colaborador (RH)
    # O backref 'cargo_ref' permite acessar o cargo a partir do colaborador (colab.cargo_ref.nome)
    colaboradores = db.relationship('Colaborador', backref='cargo_ref', lazy=True)

    def __repr__(self):
        return f"{self.nome}"