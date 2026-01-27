from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, DecimalField, SelectMultipleField, widgets
from wtforms.validators import DataRequired, Optional, Email, Length, EqualTo
from flask_wtf.file import FileField, FileAllowed, FileRequired

# Widget personalizado para transformar SelectMultiple em Checkboxes
class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class FormularioLogin(FlaskForm):
    usuario = StringField('Usuário', validators=[DataRequired()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    lembrar_de_mim = BooleanField('Lembrar de mim')
    submit = SubmitField('Entrar')

class FormularioCadastroUsuario(FlaskForm):
    nome = StringField('Nome Completo', validators=[DataRequired()])
    
    usuario = StringField('Login (Usuário)', validators=[DataRequired(), Length(min=3)])
    
    # Email Opcional, mas se preenchido, valida o formato
    email = StringField('Email', validators=[Optional(), Email()])
    
    cpf = StringField('CPF', validators=[Optional()])
    telefone = StringField('Telefone', validators=[Optional()])
    
    # Cargo como SelectField (As opções são ajustadas dinamicamente na rota)
    cargo = SelectField('Cargo', choices=[
        ('tecnico', 'Técnico'),
        ('coordenador', 'Coordenador'),
        ('gerente', 'Gerente'),
        ('dono', 'Dono')
    ], validators=[DataRequired()])

    equipe = SelectField('Equipe / Departamento', choices=[
        ('vendas', 'Vendas (Possui Meta)'),
        ('estoque', 'Estoque / Logística'),
        ('financeiro', 'Financeiro'),
        ('rh', 'Recursos Humanos'),
        ('admin', 'Administração / TI')
    ], validators=[DataRequired()])
    
    # Checkboxes de Permissão (Módulos)
    modulos_acesso = MultiCheckboxField(
        'Permissões de Acesso', 
        coerce=int,
        validators=[Optional()]
    )
    
    salario = DecimalField('Salário (R$)', places=2, validators=[Optional()])
    
    # Senha Opcional (A rota de cadastro obriga, a de edição permite vazio)
    senha = PasswordField('Senha', validators=[
        Optional(), 
        Length(min=6, message="A senha deve ter pelo menos 6 caracteres")
    ])
    
    # Novo campo para Ativar/Desativar usuário
    ativo = BooleanField('Usuário Ativo?', default=True)
    
    botao_submit = SubmitField('Salvar Funcionário')

class FormularioDocumento(FlaskForm):
    arquivo = FileField('Selecione o Arquivo', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf', 'doc', 'docx'], 'Apenas imagens e documentos PDF/Word!')
    ])
    descricao = StringField('Descrição / Nome do Documento', validators=[DataRequired()])
    submit = SubmitField('Enviar Documento')