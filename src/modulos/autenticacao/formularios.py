from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, DecimalField, SelectMultipleField, widgets
from wtforms.validators import DataRequired, Optional

class FormularioLogin(FlaskForm):
    usuario = StringField('Usuário', validators=[DataRequired()])
    senha = PasswordField('Senha', validators=[DataRequired()])
    lembrar_de_mim = BooleanField('Lembrar de mim')
    botao_submit = SubmitField('Entrar')

# Widget personalizado para transformar SelectMultiple em Checkboxes
class CheckboxWidget(widgets.ListWidget):
    template = """
        <ul class="list-unstyled mb-0">
        {% for subfield in field %}
            <li class="form-check form-check-inline">
                {{ subfield(class_="form-check-input") }} 
                {{ subfield.label(class_="form-check-label") }}
            </li>
        {% endfor %}
        </ul>"""

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

    equipe = SelectField('Equipe / Departamento', choices=[
        ('vendas', 'Vendas (Possui Meta)'),
        ('estoque', 'Estoque / Logística'),
        ('financeiro', 'Financeiro'),
        ('rh', 'Recursos Humanos'),
        ('admin', 'Administração / TI')
    ], validators=[DataRequired()])
    # NOVOS CHECKBOXES DE PERMISSÃO
    modulos_acesso = SelectMultipleField(
        'Permissões de Acesso', 
        coerce=int, # Envia o ID do módulo
        widget=CheckboxWidget(), 
        option_widget=widgets.CheckboxInput()
    )
    
    salario = DecimalField('Salário (R$)', places=2, validators=[Optional()])
    senha = PasswordField('Senha Inicial', validators=[DataRequired()])
    botao_submit = SubmitField('Salvar Funcionário')