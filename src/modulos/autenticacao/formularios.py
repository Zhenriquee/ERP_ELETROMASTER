from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired

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