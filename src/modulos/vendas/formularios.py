from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, TextAreaField, IntegerField, RadioField, HiddenField, SubmitField, DateField
from wtforms.validators import DataRequired, Optional

class FormularioVendaWizard(FlaskForm):
    # Etapa 1: Cliente
    tipo_cliente = RadioField('Tipo', choices=[('PF', 'Pessoa Física'), ('PJ', 'Pessoa Jurídica')], default='PF')
    
    # Campos PF
    pf_nome = StringField('Nome Completo')
    pf_cpf = StringField('CPF')
    
    # Campos PJ
    pj_fantasia = StringField('Nome Fantasia')
    pj_solicitante = StringField('Nome do Solicitante')
    pj_cnpj = StringField('CNPJ')
    
    # Comuns
    telefone = StringField('Telefone', validators=[DataRequired()])
    email = StringField('Email')
    endereco = StringField('Endereço Completo')

    # Etapa 2: Serviço
    descricao_servico = TextAreaField('Descrição do Serviço', validators=[DataRequired()])
    observacoes_internas = TextAreaField('Obs. Internas')

    # Etapa 3 e 4
    cor_id = SelectField('Cor / Acabamento', coerce=int, validators=[DataRequired()])
    tipo_medida = SelectField('Tipo Metragem', choices=[('m2', 'Quadrada (m²)'), ('m3', 'Cúbica (m³)')])
    
    dim_1 = DecimalField('Dimensão 1', places=2)
    dim_2 = DecimalField('Dimensão 2', places=2)
    dim_3 = DecimalField('Dimensão 3', places=2, validators=[Optional()])
    
    metragem_calculada = HiddenField('Metragem Total')
    qtd_pecas = IntegerField('Qtd. Peças', default=1, validators=[DataRequired()])

    # Etapa 5
    tipo_desconto = RadioField('Tipo Desconto', choices=[('sem', 'Sem Desconto'), ('perc', '%'), ('real', 'R$')], default='sem')
    input_desconto = DecimalField('Valor Desconto', default=0)
    input_acrescimo = DecimalField('Acréscimo Técnico (R$)', default=0) # <--- Novo
    
    valor_final_hidden = HiddenField('Valor Final')

class FormularioPagamento(FlaskForm):
    tipo_recebimento = RadioField('Tipo', choices=[('parcial', 'Recebimento Parcial'), ('total', 'Quitar Restante')], default='parcial')
    valor = DecimalField('Valor Recebido (R$)', places=2, validators=[Optional()])
    data_pagamento = DateField('Data do Recebimento', format='%Y-%m-%d', validators=[DataRequired()])
    # Campo oculto para controle
    valor_restante_hidden = HiddenField()