from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Optional, Length, Email

class FormularioLogin(FlaskForm):
    usuario = StringField('Usuário', validators=[DataRequired()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    lembrar_de_mim = BooleanField('Lembrar de mim')
    submit = SubmitField('Entrar')

class FormularioUsuario(FlaskForm):
    # Usado na edição de usuários já existentes
    usuario = StringField('Login de Acesso', validators=[DataRequired(), Length(min=3)])
    email = StringField('E-mail de Recuperação', validators=[Optional(), Email()])
    
    senha = PasswordField('Senha', validators=[Optional(), Length(min=6)])
    
    ativo = BooleanField('Acesso Ativo no Sistema', default=True)
    
    submit = SubmitField('Salvar Acesso')

class FormularioCriarAcesso(FlaskForm):
    # Usado na criação de novos usuários vinculados a colaboradores
    colaborador_id = SelectField('Colaborador', coerce=int, validators=[DataRequired()])
    usuario = StringField('Login', validators=[DataRequired(), Length(min=3)])
    senha = PasswordField('Senha Provisória', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Criar Conta')