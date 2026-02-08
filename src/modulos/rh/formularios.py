from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, SelectField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Optional, Length, Email

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
    
    ativo = BooleanField('Colaborador Ativo na Empresa', default=True)
    
    submit = SubmitField('Salvar Colaborador')