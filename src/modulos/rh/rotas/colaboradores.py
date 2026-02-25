from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import calendar 

from src.extensoes import banco_de_dados as db
from src.modulos.autenticacao.permissoes import cargo_exigido
from src.modulos.rh import bp_rh

# Modelos
from src.modulos.rh.modelos import Colaborador
from src.modulos.corporativo.modelos import Cargo
from src.modulos.financeiro.modelos import Despesa

# Formulários
from src.modulos.rh.formularios import FormularioColaborador

def sincronizar_financeiro_rh(colaborador):
    """
    Sincroniza o financeiro com o status do colaborador.
    Se inativo: apaga os lançamentos apenas a partir do próximo mês (mantém os do mês atual).
    Se ativo: apaga os lançamentos futuros e recria as previsões com os dados atualizados.
    """
    try:
        hoje = date.today()
        janela_meses = 6
        
        # Descobre o primeiro dia do próximo mês
        if hoje.month == 12:
            inicio_proximo_mes = date(hoje.year + 1, 1, 1)
        else:
            inicio_proximo_mes = date(hoje.year, hoje.month + 1, 1)

        # ==========================================
        # 1. SE INATIVO (DESLIGADO)
        # ==========================================
        if not colaborador.ativo:
            lancamentos_futuros = Despesa.query.filter(
                Despesa.colaborador_id == colaborador.id,
                Despesa.origem == 'rh_automatico',
                Despesa.status == 'pendente',
                Despesa.data_vencimento >= inicio_proximo_mes
            ).all()

            for desp in lancamentos_futuros:
                db.session.delete(desp)

            return "Colaborador inativo. Previsões de salário do próximo mês em diante canceladas."

        # ==========================================
        # 2. SE ATIVO (GERAÇÃO/ATUALIZAÇÃO NORMAL)
        # ==========================================
        lancamentos_futuros = Despesa.query.filter(
            Despesa.colaborador_id == colaborador.id,
            Despesa.origem == 'rh_automatico',
            Despesa.status == 'pendente',
            Despesa.data_vencimento >= hoje
        ).all()

        for desp in lancamentos_futuros:
            db.session.delete(desp)

        valor_base = float(colaborador.salario_base or 0)
        if valor_base <= 0: return "Salário zerado. Nada gerado."

        novos_criados = 0
        lista_novos = []

        def get_data_segura(ano, mes, dia_preferido):
            _, ultimo_dia = calendar.monthrange(ano, mes)
            dia_real = min(dia_preferido, ultimo_dia)
            return date(ano, mes, dia_real)

        if colaborador.frequencia_pagamento == 'mensal':
            try: dia_venc = int(colaborador.dia_pagamento)
            except: dia_venc = 5
            for i in range(janela_meses):
                data_ref = hoje + relativedelta(months=i)
                vencimento = get_data_segura(data_ref.year, data_ref.month, dia_venc)
                if vencimento > hoje:
                    lista_novos.append((vencimento, valor_base, "Salário Mensal"))

        elif colaborador.frequencia_pagamento == 'quinzenal':
            try:
                partes = colaborador.dia_pagamento.split(',')
                dia1 = int(partes[0])
                dia2 = int(partes[1]) if len(partes) > 1 else 30
            except: dia1, dia2 = 15, 30
            
            perc = colaborador.percentual_adiantamento or 40
            val_adianta = valor_base * (perc / 100)
            val_saldo = valor_base - val_adianta

            for i in range(janela_meses):
                data_ref = hoje + relativedelta(months=i)
                venc1 = get_data_segura(data_ref.year, data_ref.month, dia1)
                venc2 = get_data_segura(data_ref.year, data_ref.month, dia2)
                if venc1 > hoje: lista_novos.append((venc1, val_adianta, f"Adiantamento ({perc}%)"))
                if venc2 > hoje: lista_novos.append((venc2, val_saldo, "Saldo Salário"))

        elif colaborador.frequencia_pagamento == 'semanal':
            try: dia_semana = int(colaborador.dia_pagamento)
            except: dia_semana = 4
            val_semana = valor_base / 4 
            cursor = hoje
            while cursor.weekday() != dia_semana: cursor += timedelta(days=1)
            for _ in range(24):
                cursor += timedelta(weeks=1)
                lista_novos.append((cursor, val_semana, "Pagamento Semanal"))

        for dt_venc, valor, sulfixo in lista_novos:
            nova_despesa = Despesa(
                descricao=f"{sulfixo} - {colaborador.nome_completo}",
                valor=valor,
                categoria="salarios",
                tipo_custo="fixo",
                data_competencia=dt_venc.replace(day=1),
                data_vencimento=dt_venc,
                status="pendente",
                forma_pagamento="pix" if colaborador.chave_pix else "transferencia",
                observacao=f"Gerado Automaticamente.\nChave Pix: {colaborador.chave_pix or 'N/D'}\nBanco: {colaborador.banco or '-'}",
                colaborador_id=colaborador.id,
                usuario_id=current_user.id,
                origem='rh_automatico'
            )
            db.session.add(nova_despesa)
            novos_criados += 1

        return f"Sincronizado. {novos_criados} previsões geradas."

    except Exception as e:
        print(f"Erro sync RH: {e}")
        return "Erro ao sincronizar financeiro."


# ==============================================================
# ROTAS COM PERMISSÕES CIRÚRGICAS APLICADAS
# ==============================================================

@bp_rh.route('/', methods=['GET'])
@login_required
@cargo_exigido('rh_acesso') # APENAS VER A LISTA
def listar_colaboradores():
    colaboradores = Colaborador.query.order_by(Colaborador.ativo.desc(), Colaborador.nome_completo).all()
    return render_template('rh/lista_colaboradores.html', colaboradores=colaboradores)


@bp_rh.route('/novo', methods=['GET', 'POST'])
@login_required
@cargo_exigido('rh_criar') # APENAS CRIAR
def novo_colaborador():
    form = FormularioColaborador()
    cargos_db = Cargo.query.filter_by(ativo=True).order_by(Cargo.nome).all()
    form.cargo_id.choices = [(c.id, f"{c.nome} - {c.setor.nome}") for c in cargos_db]
    if not form.cargo_id.choices: form.cargo_id.choices = [(0, 'Cadastre cargos no módulo Corporativo')]

    if form.validate_on_submit():
        if Colaborador.query.filter_by(cpf=form.cpf.data).first():
            flash('Este CPF já está cadastrado.', 'error')
        else:
            novo = Colaborador(
                nome_completo=form.nome_completo.data,
                cpf=form.cpf.data,
                rg=form.rg.data,
                data_nascimento=form.data_nascimento.data,
                email_pessoal=form.email_pessoal.data,
                telefone=form.telefone.data,
                endereco=form.endereco.data,
                cargo_id=form.cargo_id.data,
                data_admissao=form.data_admissao.data,
                tipo_contrato=form.tipo_contrato.data,
                salario_base=form.salario_base.data,
                ativo=form.ativo.data,
                faz_parte_meta=form.faz_parte_meta.data,
                chave_pix=form.chave_pix.data,
                banco=form.banco.data,
                agencia=form.agencia.data,
                conta=form.conta.data,
                frequencia_pagamento=form.frequencia_pagamento.data,
                dia_pagamento=form.dia_pagamento.data,
                percentual_adiantamento=form.percentual_adiantamento.data
            )
            db.session.add(novo)
            db.session.flush()
            
            msg_sync = sincronizar_financeiro_rh(novo)
            db.session.commit()
            flash(f'Colaborador cadastrado! {msg_sync}', 'success')
            return redirect(url_for('rh.listar_colaboradores'))

    return render_template('rh/cadastro_colaborador.html', form=form, titulo="Novo Colaborador")


@bp_rh.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@cargo_exigido('rh_editar') # APENAS EDITAR
def editar_colaborador(id):
    colab = Colaborador.query.get_or_404(id)
    form = FormularioColaborador(obj=colab)
    
    cargos_db = Cargo.query.order_by(Cargo.nome).all()
    form.cargo_id.choices = [(c.id, f"{c.nome} - {c.setor.nome}") for c in cargos_db]

    if form.validate_on_submit():
        existente = Colaborador.query.filter(Colaborador.cpf == form.cpf.data, Colaborador.id != id).first()
        if existente:
            flash('Este CPF já pertence a outro colaborador.', 'error')
        else:
            form.populate_obj(colab) 
            msg_sync = sincronizar_financeiro_rh(colab)
            db.session.commit()
            flash(f'Dados atualizados. {msg_sync}', 'success')
            return redirect(url_for('rh.listar_colaboradores'))

    return render_template('rh/cadastro_colaborador.html', form=form, titulo="Editar Colaborador", editando=True)


@bp_rh.route('/perfil/<int:id>')
@login_required
@cargo_exigido('rh_acesso') # ACESSO BÁSICO DE VISUALIZAÇÃO
def perfil_colaborador(id):
    colab = Colaborador.query.get_or_404(id)
    return render_template('rh/perfil_colaborador.html', colab=colab)


# NOVA ROTA: SEPARADA PARA GARANTIR A PERMISSÃO DE STATUS
@bp_rh.route('/status/<int:id>', methods=['POST'])
@login_required
@cargo_exigido('rh_status') # APENAS MUDAR STATUS
def alternar_status_colaborador(id):
    colab = Colaborador.query.get_or_404(id)
    
    # Inverte o status atual
    colab.ativo = not colab.ativo
    
    # Chama o financeiro para apagar as contas se inativado
    msg_sync = sincronizar_financeiro_rh(colab)
    
    db.session.commit()
    
    status_texto = "Reativado" if colab.ativo else "Inativado (Demitido)"
    flash(f'Colaborador {status_texto} com sucesso! {msg_sync}', 'success')
    
    return redirect(url_for('rh.listar_colaboradores'))