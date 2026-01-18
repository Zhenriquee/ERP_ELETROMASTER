from flask_wtf import FlaskForm
from wtforms import IntegerField, DecimalField, SelectField, SelectMultipleField, StringField, widgets
from wtforms.validators import DataRequired, Optional, ValidationError
from datetime import datetime

# Widget personalizado para Checkbox Múltiplo
class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class FormularioMetaLoja(FlaskForm):
    mes = SelectField('Mês', choices=[
        (1, 'Janeiro'), (2, 'Fevereiro'), (3, 'Março'), (4, 'Abril'),
        (5, 'Maio'), (6, 'Junho'), (7, 'Julho'), (8, 'Agosto'),
        (9, 'Setembro'), (10, 'Outubro'), (11, 'Novembro'), (12, 'Dezembro')
    ], coerce=int, validators=[DataRequired()], default=datetime.now().month)
    
    ano = IntegerField('Ano', default=datetime.now().year, validators=[DataRequired()])
    
    valor_loja = DecimalField('Meta Global da Loja (R$)', places=2, validators=[DataRequired()])
    
    # CORREÇÃO: Removemos 'DataRequired()' daqui para tirar o 'required' do HTML
    dias_semana = MultiCheckboxField('Dias de Trabalho', choices=[
        ('0', 'Segunda'), ('1', 'Terça'), ('2', 'Quarta'), 
        ('3', 'Quinta'), ('4', 'Sexta'), ('5', 'Sábado'), ('6', 'Domingo')
    ], default=['0','1','2','3','4']) 
    
    feriados = StringField('Feriados / Folgas (Dias)', 
                           validators=[Optional()],
                           render_kw={"placeholder": "Ex: 1, 25"})

    # Validação Personalizada 1: Garante que pelo menos um dia foi selecionado
    def validate_dias_semana(self, field):
        if not field.data or len(field.data) == 0:
            raise ValidationError('Selecione pelo menos um dia da semana.')

    # Validação Personalizada 2: Valida os dias do mês no campo de feriados
    def validate_feriados(self, field):
        if not field.data:
            return
        
        # Remove espaços e divide
        partes = field.data.replace(' ', '').split(',')
        
        for p in partes:
            if not p: continue 
            
            if not p.isdigit():
                raise ValidationError(f'"{p}" não é válido. Use apenas números.')
            
            dia = int(p)
            if dia < 1 or dia > 31:
                raise ValidationError(f'O dia {dia} é inválido (deve ser entre 1 e 31).')

class FormularioMetaIndividual(FlaskForm):
    usuario_id = IntegerField('ID Usuário')
    valor_meta = DecimalField('Meta Individual', places=2)