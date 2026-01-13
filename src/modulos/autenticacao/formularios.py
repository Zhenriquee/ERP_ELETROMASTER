from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, DecimalField
from wtforms.validators import DataRequired, Optional

class FormularioLogin(FlaskForm):
    # Mudança aqui: Campo Usuario em vez de Email
    usuario = StringField('Usuário', validators=[
        DataRequired(message="O usuário é obrigatório")
    ])
    senha = PasswordField('Senha', validators=[
        DataRequired(message="A senha é obrigatória")
    ])
    lembrar_de_mim = BooleanField('Lembrar de mim')
    botao_submit = SubmitField('Entrar')

class FormularioCadastroUsuario(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired()])
    usuario = StringField('Login (Usuário)', validators=[DataRequired()])
    cpf = StringField('CPF', validators=[DataRequired()])
    telefone = StringField('Telefone', validators=[DataRequired()])
    email = StringField('Email', validators=[Optional()])
    
    cargo = SelectField('Cargo', choices=[
        ('tecnico', 'Técnico'),
        ('coordenador', 'Coordenador'),
        ('gerente', 'Gerente'),
        ('dono', 'Dono')
    ], validators=[DataRequired()])
    
    salario = DecimalField('Salário (R$)', places=2, validators=[Optional()])
    
    senha = PasswordField('Senha Inicial', validators=[DataRequired()])
    botao_submit = SubmitField('Cadastrar Funcionário')    