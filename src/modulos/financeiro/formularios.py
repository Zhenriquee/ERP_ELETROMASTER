from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, SelectField, TextAreaField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from src.modulos.estoque.modelos import ProdutoEstoque # Importe no topo

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

    # --- NOVO CAMPO: Decisor do Tipo de Despesa ---
    eh_compra_produto = BooleanField('É compra de material para estoque?')
    
    # Campos de Estoque (Validadores Opcionais pois só usamos se o checkbox acima estiver marcado)
    produto_estoque_id = SelectField('Produto (Estoque)', coerce=int, validators=[Optional()])
    qtd_estoque = DecimalField('Quantidade Comprada', places=3, validators=[Optional()])

    descricao = StringField('Descrição', validators=[Optional(), Length(max=100)])
    
    # Valores e Datas
    valor = DecimalField('Valor (R$)', places=2, validators=[DataRequired()])
    data_vencimento = DateField('Data de Vencimento', format='%Y-%m-%d', validators=[DataRequired()])
    
    # REMOVIDO: data_competencia = StringField(...) -> Agora é automático no backend
    
    # Data de Pagamento
    data_pagamento = DateField('Data do Pagamento', format='%Y-%m-%d', validators=[Optional()])

    categoria = SelectField('Categoria', choices=[
        ('infraestrutura', 'Infraestrutura (Aluguel, Energia, Água, Internet)'),
        ('pessoal', 'Pessoal (Salários, Pró-labore, Vale, Benefícios)'),
        ('material', 'Material / Insumos (Matéria-prima, Embalagens, Estoque)'),
        ('impostos', 'Impostos / Taxas (DAS, ICMS, ISS, IPTU)'),
        ('financeiro', 'Despesa Financeira (Tarifas Bancárias, Juros, Multas)'),
        ('manutencao', 'Manutenção (Reparos, Limpeza, Pintura, TI)'),
        ('marketing', 'Marketing (Anúncios, Redes Sociais, Brindes, Site)'),
        ('outros', 'Outros (Despesas Diversas / Não Classificadas)')
    ], validators=[DataRequired()])
    
    # ALTERADO: Adicionada opção 'extra'
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

    recorrente = BooleanField('Despesa Recorrente?')
    qtd_repeticoes = IntegerField('Repetir por quantos meses?', 
                                  default=1, 
                                  validators=[Optional(), NumberRange(min=1, max=60)])