from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, SubmitField
from wtforms.validators import DataRequired

class FormularioProduto(FlaskForm):
    nome = StringField('Nome do Acabamento/Serviço', validators=[DataRequired()])
    unidade = SelectField('Unidade de Medida', choices=[
        ('m2', 'Metro Quadrado (m²)'), 
        ('m3', 'Metro Cúbico (m³)')
    ], validators=[DataRequired()])
    preco = DecimalField('Preço Unitário (R$)', places=2, validators=[DataRequired()])
    submit = SubmitField('Salvar')