from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, TextAreaField, widgets, SelectMultipleField
from wtforms.validators import DataRequired, Optional

# Widget para checkboxes
class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class FormularioSetor(FlaskForm):
    nome = StringField('Nome do Setor', validators=[DataRequired()])
    descricao = TextAreaField('Descrição', validators=[Optional()])
    submit = SubmitField('Salvar Setor')

class FormularioCargo(FlaskForm):
    nome = StringField('Nome do Cargo', validators=[DataRequired()])
    setor_id = SelectField('Setor', coerce=int, validators=[DataRequired()])
    
    nivel_hierarquico = SelectField('Nível Hierárquico', choices=[
        (1, 'Nível 1 - Direção / Dono'),
        (2, 'Nível 2 - Gerência'),
        (3, 'Nível 3 - Coordenação / Líder'),
        (4, 'Nível 4 - Operacional / Técnico')
    ], coerce=int, default=4)
    
    descricao = TextAreaField('Descrição', validators=[Optional()])
    
    # Campo de Permissões
    permissoes = MultiCheckboxField('Permissões de Acesso', coerce=int, validators=[Optional()])
    
    submit = SubmitField('Salvar Cargo')