from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, SelectField, SubmitField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Optional, Length, Email
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms.validators import NumberRange # Importe NumberRange

class FormularioColaborador(FlaskForm):
    # --- DADOS PESSOAIS ---
    nome_completo = StringField('Nome Completo', validators=[DataRequired(), Length(max=150)])
    cpf = StringField('CPF', validators=[DataRequired(), Length(min=11, max=14)])
    rg = StringField('RG', validators=[Optional(), Length(max=20)])
    data_nascimento = DateField('Data de Nascimento', format='%Y-%m-%d', validators=[Optional()])
    
    # --- CONTATO ---
    email_pessoal = StringField('E-mail Pessoal', validators=[Optional(), Email()])
    telefone = StringField('Telefone / WhatsApp', validators=[Optional()])
    endereco = StringField('Endereço Completo', validators=[Optional()])
    
    # --- CONTRATUAL ---
    # O choices é populado na rota (backend) buscando do banco de dados
    cargo_id = SelectField('Cargo / Função', coerce=int, validators=[DataRequired()])
    
    data_admissao = DateField('Data de Admissão', format='%Y-%m-%d', validators=[DataRequired()])
    
    tipo_contrato = SelectField('Tipo de Contrato', choices=[
        ('CLT', 'CLT (Carteira Assinada)'),
        ('PJ', 'PJ (Prestador de Serviço)'),
        ('Estagio', 'Estagiário'),
        ('Temporario', 'Temporário'),
        ('Socio', 'Sócio / Dono')
    ], validators=[DataRequired()])
    
    salario_base = DecimalField('Salário Base (R$)', places=2, validators=[Optional()])
    
    # --- DADOS BANCÁRIOS & PAGAMENTO (FALTAVA ISSO) ---
    chave_pix = StringField('Chave Pix', validators=[Optional()])
    banco = StringField('Banco', validators=[Optional()])
    agencia = StringField('Agência', validators=[Optional()])
    conta = StringField('Conta', validators=[Optional()])
    
    frequencia_pagamento = SelectField('Frequência de Pagamento', choices=[
        ('mensal', 'Mensal (1x por mês)'),
        ('quinzenal', 'Quinzenal (2x por mês)'),
        ('semanal', 'Semanal (Toda semana)')
    ], default='mensal')
    
    # Campo que armazena os dias (ex: "5" ou "5,20")
    dia_pagamento = StringField('Dia(s) do Pagamento', validators=[Optional()])
    # NOVO CAMPO: Porcentagem do Vale/Adiantamento
    percentual_adiantamento = IntegerField(
        '% do Adiantamento (1ª Parcela)', 
        default=40,
        validators=[Optional(), NumberRange(min=1, max=99)]
    )
    percentual_desconto = DecimalField('Desconto Fixo (%)', places=2, default=0.00, validators=[Optional()]) # NOVO CAMPO
    
    
    
    ativo = BooleanField('Colaborador Ativo na Empresa', default=True)
    
    # --- NOVO CAMPO NO FORMULÁRIO ---
    faz_parte_meta = BooleanField('Participa de Metas', default=False)
    
    submit = SubmitField('Salvar Colaborador')

class FormularioDocumentoRH(FlaskForm):
    arquivo = FileField('Arquivo', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'], 'Apenas PDF, Imagens ou Word.')
    ])
    descricao = StringField('Tipo do Documento', validators=[DataRequired()], render_kw={"placeholder": "Ex: RG, CNH, Contrato..."})
    submit = SubmitField('Anexar Documento')