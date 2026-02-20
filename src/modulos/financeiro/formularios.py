from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, SelectField, TextAreaField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from src.modulos.estoque.modelos import ProdutoEstoque
from datetime import date

class FormularioFornecedor(FlaskForm):
    nome_fantasia = StringField('Nome Fantasia', validators=[DataRequired(), Length(min=2, max=100)])
    razao_social = StringField('Razão Social', validators=[Optional(), Length(max=100)])
    cnpj = StringField('CNPJ', validators=[Optional(), Length(max=20)])
    telefone = StringField('Telefone', validators=[Optional(), Length(max=20)])
    email = StringField('E-mail', validators=[Optional(), Length(max=100)])
    cidade = StringField('Cidade', validators=[Optional(), Length(max=50)])
    estado = SelectField('Estado', choices=[
        ('', 'Selecione...'), ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
        ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
        ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
        ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins')
    ], validators=[Optional()])

class FormularioDespesa(FlaskForm):

    # --- CAMPO DECISOR ---
    eh_compra_produto = BooleanField('É compra de material para estoque?')
    
    # OBS: Os campos de produto único (produto_estoque_id, qtd_estoque) foram removidos da validação
    # pois agora os produtos virão via lista dinâmica no request.form
    
    descricao = StringField('Descrição', validators=[Optional(), Length(max=100)])
    
    # Valores e Datas
    valor = DecimalField('Valor Total (R$)', places=2, validators=[DataRequired()])
    
    data_compra = DateField('Data da Compra', format='%Y-%m-%d', default=date.today, validators=[DataRequired()])
    data_vencimento = DateField('Data de Vencimento (1ª Parcela)', format='%Y-%m-%d', validators=[DataRequired()])
    
    # Data de Pagamento (Se pago)
    data_pagamento = DateField('Data do Pagamento', format='%Y-%m-%d', validators=[Optional()])

    # Categorias
    categoria = SelectField('Categoria', choices=[
        ('salarios', 'Salários & Folha de Pagamento'),
        ('pessoal', 'Retiradas / Pessoal (Sócios)'),
        ('infraestrutura', 'Infraestrutura (Aluguel, Energia, Água)'),
        ('material', 'Material / Insumos'),
        ('impostos', 'Impostos / Taxas'),
        ('financeiro', 'Despesa Financeira'),
        ('manutencao', 'Manutenção'),
        ('marketing', 'Marketing'),
        ('outros', 'Outros')
    ], validators=[DataRequired()])
    
    tipo_custo = SelectField('Tipo de Custo', choices=[
        ('fixo', 'Custo Fixo (Recorrente)'),
        ('variavel', 'Custo Variável (Produção/Venda)'),
        ('extra', 'Custo Extra')
    ], validators=[DataRequired()])
    
    forma_pagamento = SelectField('Forma de Pagamento', choices=[
        ('boleto', 'Boleto Bancário'),
        ('pix', 'Pix'),
        ('transferencia', 'Transferência (TED/DOC)'),
        ('cartao_credito', 'Cartão de Crédito'),
        ('dinheiro', 'Dinheiro / Espécie'),
        ('debito_automatico', 'Débito Automático')
    ], validators=[DataRequired()])
    
    status = SelectField('Status Atual', choices=[
        ('pendente', 'Pendente (A Pagar)'),
        ('pago', 'Pago')
    ], default='pendente')
    
    fornecedor_id = SelectField('Fornecedor (Opcional)', coerce=int, validators=[Optional()])
    usuario_id = SelectField('Funcionário/Sócio (Opcional)', coerce=int, validators=[Optional()])
    
    codigo_barras = StringField('Código de Barras / Chave Pix', validators=[Optional()])
    observacao = TextAreaField('Observações', validators=[Optional()])

    recorrente = BooleanField('Parcelar / Repetir?')
    qtd_repeticoes = IntegerField('Nº Parcelas / Meses', 
                                  default=1, 
                                  validators=[Optional(), NumberRange(min=1, max=60)])