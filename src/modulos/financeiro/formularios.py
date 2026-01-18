from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, SelectField, TextAreaField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Optional, Length, NumberRange

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
    descricao = StringField('Descrição da Despesa', validators=[DataRequired(), Length(min=3, max=100)])
    
    # Valores e Datas
    valor = DecimalField('Valor (R$)', places=2, validators=[DataRequired()])
    data_vencimento = DateField('Data de Vencimento', format='%Y-%m-%d', validators=[DataRequired()])
    
    # Data de Competência (String para suportar type="month")
    data_competencia = StringField('Mês de Competência', validators=[DataRequired()])
    
    # Data de Pagamento (Novo campo para edição/visualização)
    data_pagamento = DateField('Data do Pagamento', format='%Y-%m-%d', validators=[Optional()])

    categoria = SelectField('Categoria', choices=[
        ('infraestrutura', 'Infraestrutura (Luz, Água, Aluguel)'),
        ('pessoal', 'Pessoal (Salários, Vale, Pró-labore)'),
        ('material', 'Material / Insumos'),
        ('impostos', 'Impostos / Taxas'),
        ('financeiro', 'Despesa Financeira / Tarifas'),
        ('manutencao', 'Manutenção / Limpeza'),
        ('marketing', 'Marketing / Publicidade'),
        ('outros', 'Outros')
    ], validators=[DataRequired()])
    
    tipo_custo = SelectField('Tipo de Custo', choices=[
        ('fixo', 'Custo Fixo (Recorrente)'),
        ('variavel', 'Custo Variável (Produção/Venda)')
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

    # Recorrência (Correção do Bug: min=1)
    recorrente = BooleanField('Despesa Recorrente?')
    qtd_repeticoes = IntegerField('Repetir por quantos meses?', 
                                  default=1, 
                                  validators=[Optional(), NumberRange(min=1, max=60)])