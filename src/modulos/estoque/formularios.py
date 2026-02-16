from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Optional

class FormularioProdutoEstoque(FlaskForm):
    nome = StringField('Nome do Produto', validators=[DataRequired()])
    
    unidade = SelectField('Unidade', choices=[
        ('KG', 'Quilograma (KG)'), 
        ('G', 'Grama (G)'),
        ('L', 'Litro (L)'),
        ('UN', 'Unidade (UN)')
    ], default='KG', validators=[DataRequired()])
    
    quantidade_atual = DecimalField('Quantidade Atual', places=3, validators=[Optional()])
    quantidade_minima = DecimalField('Estoque Mínimo (Alerta)', places=3, default=5.0)
    
    # Preços continuam com 2 casas (financeiro)
    preco_m2 = DecimalField('Preço de Venda por m² (R$)', places=2, validators=[Optional()])
    preco_m3 = DecimalField('Preço de Venda por m³ (R$)', places=2, validators=[Optional()])

    # Consumo agora com 3 casas (Físico)
    consumo_m2 = DecimalField('Consumo Médio por m²', places=3, default=0)
    consumo_m3 = DecimalField('Consumo Médio por m³', places=3, default=0)
    
    submit = SubmitField('Salvar Produto')

class FormularioMovimentacaoManual(FlaskForm):
    tipo = SelectField('Tipo', choices=[('entrada', 'Entrada (Adicionar)'), ('saida', 'Saída (Baixar)')], validators=[DataRequired()])
    quantidade = DecimalField('Quantidade', places=3, validators=[DataRequired()])
    observacao = TextAreaField('Motivo / Observação', validators=[Optional()])
    submit = SubmitField('Registrar Movimentação')