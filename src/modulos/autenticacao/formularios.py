from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Optional, Length, Email
from flask_wtf.file import FileField, FileAllowed, FileRequired

class FormularioLogin(FlaskForm):
    usuario = StringField('Usuário', validators=[DataRequired()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    lembrar_de_mim = BooleanField('Lembrar de mim')
    submit = SubmitField('Entrar')

# --- NOVO: Formulário Simplificado para Edição ---
class FormularioUsuario(FlaskForm):
    usuario = StringField('Login de Acesso', validators=[DataRequired(), Length(min=3)])
    email = StringField('E-mail de Recuperação', validators=[Optional(), Email()])
    
    # Senha opcional (só preenche se quiser mudar)
    senha = PasswordField('Nova Senha', validators=[Optional(), Length(min=6)])
    
    # Ativo só aparece para o Dono no template
    ativo = BooleanField('Acesso Ativo', default=True)
    
    submit = SubmitField('Salvar Alterações')

class FormularioCriarAcesso(FlaskForm):
    # Dropdown que lista apenas colaboradores SEM usuário
    colaborador_id = SelectField('Colaborador', coerce=int, validators=[DataRequired()])
    usuario = StringField('Login', validators=[DataRequired(), Length(min=3)])
    senha = PasswordField('Senha Provisória', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Criar Conta')

class FormularioDocumento(FlaskForm):
    arquivo = FileField('Arquivo', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'], 'Apenas PDF, Imagens ou Word.')
    ])
    descricao = StringField('Descrição', validators=[DataRequired()])
    submit = SubmitField('Anexar')