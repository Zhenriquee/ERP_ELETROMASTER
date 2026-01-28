from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, TextAreaField, IntegerField, RadioField, HiddenField, SubmitField, DateField
from wtforms.validators import DataRequired, Optional

class FormularioVendaWizard(FlaskForm):
    tipo_cliente = RadioField('Tipo', choices=[('PF', 'Pessoa Física'), ('PJ', 'Pessoa Jurídica')], default='PF')
    pf_nome = StringField('Nome Completo')
    pf_cpf = StringField('CPF')
    pj_fantasia = StringField('Nome Fantasia')
    pj_solicitante = StringField('Nome do Solicitante')
    pj_cnpj = StringField('CNPJ')
    telefone = StringField('Telefone', validators=[DataRequired()])
    email = StringField('Email')
    endereco = StringField('Endereço Completo')

    # --- Etapa 2: Serviço ---
    descricao_servico = TextAreaField('Descrição do Serviço', validators=[DataRequired()])
    observacoes_internas = TextAreaField('Obs. Internas')

    # --- Etapa 3 e 4: Detalhes Técnicos (ALTERADO) ---
    # Mudamos o nome para produto_id para ficar claro que vem do estoque
    produto_id = SelectField('Produto / Acabamento', coerce=int, validators=[DataRequired()])
    
    tipo_medida = SelectField('Tipo Metragem', choices=[('m2', 'Quadrada (m²)'), ('m3', 'Cúbica (m³)')], default='m2')
    
    dimensao_1 = DecimalField('Dimensão 1 (Altura)', places=2, default=0.0)
    dimensao_2 = DecimalField('Dimensão 2 (Largura)', places=2, default=0.0)
    dimensao_3 = DecimalField('Dimensão 3 (Profundidade)', places=2, validators=[Optional()], default=0.0)
    
    quantidade_pecas = IntegerField('Qtd. Peças', default=1, validators=[DataRequired()])
    
    metragem_total = HiddenField('Metragem Total')

    # --- Etapa 5: Financeiro (Mantido igual) ---
    valor_base = HiddenField('Valor Base')
    tipo_desconto = RadioField('Tipo Desconto', choices=[('sem', 'Sem Desconto'), ('perc', '%'), ('real', 'R$')], default='sem')
    valor_acrescimo = DecimalField('Acréscimo (R$)', default=0.0, places=2)
    valor_desconto_aplicado = DecimalField('Desconto Aplicado', default=0.0, places=2)
    valor_final = HiddenField('Valor Final')

    submit = SubmitField('Confirmar Venda')

class FormularioPagamento(FlaskForm):
    tipo_recebimento = RadioField('Tipo', choices=[('parcial', 'Recebimento Parcial'), ('total', 'Quitar Restante')], default='parcial')
    valor = DecimalField('Valor Recebido (R$)', places=2, validators=[Optional()])
    data_pagamento = DateField('Data do Recebimento', format='%Y-%m-%d', validators=[DataRequired()])
    # Campo oculto para controle
    valor_restante_hidden = HiddenField()