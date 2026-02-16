from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, TextAreaField, SelectMultipleField, widgets
from wtforms.validators import DataRequired, Optional

# --- Widget Personalizado para Checkbox Múltiplo ---
# Transforma uma lista de seleção múltipla em vários checkboxes visuais
class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class FormularioSetor(FlaskForm):
    nome = StringField('Nome do Setor', validators=[DataRequired()])
    descricao = TextAreaField('Descrição', validators=[Optional()])
    submit = SubmitField('Salvar Setor')

class FormularioCargo(FlaskForm):
    nome = StringField('Nome do Cargo', validators=[DataRequired()])
    
    # Select de Setor (Preenchido na rota)
    setor_id = SelectField('Setor', coerce=int, validators=[DataRequired()])
    
    nivel_hierarquico = SelectField('Nível de Acesso Sugerido', choices=[
        (1, 'Nível 1 - Direção / Dono'),
        (2, 'Nível 2 - Gerência'),
        (3, 'Nível 3 - Coordenação / Líder'),
        (4, 'Nível 4 - Operacional / Técnico')
    ], coerce=int, default=4)
    
    descricao = TextAreaField('Descrição da Função', validators=[Optional()])
    
    # --- NOVO CAMPO: PERMISSÕES ---
    # Este campo receberá a lista de módulos do sistema
    permissoes = MultiCheckboxField('Permissões de Acesso', coerce=int, validators=[Optional()])
    
    submit = SubmitField('Salvar Cargo')