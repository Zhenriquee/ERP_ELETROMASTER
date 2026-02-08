from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional

class FormularioSetor(FlaskForm):
    nome = StringField('Nome do Setor', validators=[DataRequired()])
    descricao = TextAreaField('Descrição', validators=[Optional()])
    submit = SubmitField('Salvar Setor')

class FormularioCargo(FlaskForm):
    nome = StringField('Nome do Cargo', validators=[DataRequired()])
    
    # O conteúdo deste Select é preenchido dinamicamente na rota
    setor_id = SelectField('Setor', coerce=int, validators=[DataRequired()])
    
    nivel_hierarquico = SelectField('Nível de Acesso Sugerido', choices=[
        (1, 'Nível 1 - Direção / Dono'),
        (2, 'Nível 2 - Gerência'),
        (3, 'Nível 3 - Coordenação / Líder'),
        (4, 'Nível 4 - Operacional / Técnico')
    ], coerce=int, default=4)
    
    descricao = TextAreaField('Descrição da Função', validators=[Optional()])
    submit = SubmitField('Salvar Cargo')