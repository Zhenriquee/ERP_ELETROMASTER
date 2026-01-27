from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Optional

class FormularioProdutoEstoque(FlaskForm):
    nome = StringField('Nome do Produto', validators=[DataRequired()])
    unidade = SelectField('Unidade', choices=[('CX', 'Caixa'), ('UN', 'Unidade'), ('LT', 'Litro'), ('KG', 'Quilo')], default='CX')
    estoque_minimo = DecimalField('Estoque Mínimo (Alerta)', places=3, default=0)
    submit = SubmitField('Salvar Produto')

class FormularioMovimentacaoManual(FlaskForm):
    tipo = SelectField('Tipo', choices=[('entrada', 'Entrada (Adicionar)'), ('saida', 'Saída (Baixar)')], validators=[DataRequired()])
    quantidade = DecimalField('Quantidade', places=3, validators=[DataRequired()])
    observacao = TextAreaField('Motivo / Observação', validators=[Optional()])
    submit = SubmitField('Registrar Movimentação')