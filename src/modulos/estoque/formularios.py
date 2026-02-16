from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Optional

class FormularioProdutoEstoque(FlaskForm):
    nome = StringField('Nome do Produto / Tinta', validators=[DataRequired()])
    
    # Unidades restritas
    unidade = SelectField('Unidade de Medida', choices=[
        ('KG', 'Quilograma (KG)'), 
        ('G', 'Grama (G)')
    ], default='KG', validators=[DataRequired()])
    
    # --- CONTROLE DE ESTOQUE (Campo Renomeado) ---
    quantidade_atual = DecimalField('Quantidade Atual', places=3, validators=[Optional()])
    quantidade_minima = DecimalField('Estoque Mínimo (Alerta)', places=3, default=5.0)
    
    # --- CUSTO ---
    valor_unitario = DecimalField('Custo Unitário (R$)', places=2, validators=[Optional()], 
                                description="Quanto custou para a empresa (por KG ou G)?")

    # --- PRECIFICAÇÃO DE VENDA ---
    preco_m2 = DecimalField('Preço de Venda por m² (R$)', places=2, validators=[Optional()])
    preco_m3 = DecimalField('Preço de Venda por m³ (R$)', places=2, validators=[Optional()])

    # --- FICHA TÉCNICA / CONSUMO ---
    consumo_m2 = DecimalField('Consumo Médio por m²', places=4, default=0)
    consumo_m3 = DecimalField('Consumo Médio por m³', places=4, default=0)
    
    submit = SubmitField('Salvar Produto')

class FormularioMovimentacaoManual(FlaskForm):
    tipo = SelectField('Tipo', choices=[('entrada', 'Entrada (Adicionar)'), ('saida', 'Saída (Baixar)')], validators=[DataRequired()])
    quantidade = DecimalField('Quantidade', places=3, validators=[DataRequired()])
    observacao = TextAreaField('Motivo / Observação', validators=[Optional()])
    submit = SubmitField('Registrar Movimentação')