from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Optional

class FormularioProduto(FlaskForm):
    nome = StringField('Nome do Acabamento/Serviço', validators=[DataRequired()])
    preco_m2 = DecimalField('Preço por m² (R$)', places=2, validators=[Optional()])
    preco_m3 = DecimalField('Preço por m³ (R$)', places=2, validators=[Optional()])
    submit = SubmitField('Salvar')