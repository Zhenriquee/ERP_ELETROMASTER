from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
import calendar # Adicione este import no topo
from src.extensoes import banco_de_dados as db
from src.modulos.autenticacao.permissoes import cargo_exigido
from src.modulos.rh import bp_rh

# Modelos
from src.modulos.rh.modelos import Colaborador
from src.modulos.corporativo.modelos import Cargo
from src.modulos.financeiro.modelos import Despesa

# Formulários
from src.modulos.rh.formularios import FormularioColaborador

# --- LÓGICA AUXILIAR: SINCRONIZAÇÃO FINANCEIRA ---
def sincronizar_financeiro_rh(colaborador):
    try:
        hoje = date.today()
        janela_meses = 6
        
        # 1. LIMPEZA (Igual ao anterior)
        lancamentos_futuros = Despesa.query.filter(
            Despesa.colaborador_id == colaborador.id,
            Despesa.origem == 'rh_automatico',
            Despesa.status == 'pendente',
            Despesa.data_vencimento >= hoje
        ).all()

        if not colaborador.ativo:
            for desp in lancamentos_futuros: db.session.delete(desp)
            return "Colaborador inativo. Previsões removidas."

        valor_base = float(colaborador.salario_base or 0)
        if valor_base <= 0: return "Salário zerado."

        # Mapeia o que já existe
        datas_cobertas = set()
        for desp in lancamentos_futuros:
            datas_cobertas.add(desp.data_vencimento)
            # Atualiza valor se necessário (apenas para mensal simples por enquanto)
            if colaborador.frequencia_pagamento == 'mensal' and abs(float(desp.valor) - valor_base) > 0.01:
                desp.valor = valor_base

        # 2. GERAÇÃO
        novos = 0
        lista_novos = []

        # --- FUNÇÃO AUXILIAR PARA CORRIGIR DATAS (RESOLVE O PROBLEMA DO DIA 30) ---
        def get_data_segura(ano, mes, dia_preferido):
            # calendar.monthrange retorna (dia_semana, ultimo_dia_do_mes)
            _, ultimo_dia = calendar.monthrange(ano, mes)
            
            # Se preferir dia 30, mas o mês acaba dia 28, usa 28.
            dia_real = min(dia_preferido, ultimo_dia)
            return date(ano, mes, dia_real)
        # --------------------------------------------------------------------------

        if colaborador.frequencia_pagamento == 'mensal':
            try: dia_venc = int(colaborador.dia_pagamento)
            except: dia_venc = 5

            for i in range(janela_meses):
                data_ref = hoje + relativedelta(months=i)
                vencimento = get_data_segura(data_ref.year, data_ref.month, dia_venc)
                
                if vencimento > hoje and vencimento not in datas_cobertas:
                    lista_novos.append((vencimento, valor_base, "Salário Mensal"))

        elif colaborador.frequencia_pagamento == 'quinzenal':
            try:
                # Ex: "15,30" -> dia1=15, dia2=30
                dias = [int(d) for d in colaborador.dia_pagamento.split(',')]
                dia1, dia2 = min(dias), max(dias)
            except: dia1, dia2 = 15, 30
            
            # --- CÁLCULO PROPORCIONAL DINÂMICO ---
            perc = colaborador.percentual_adiantamento or 40
            val_adianta = valor_base * (perc / 100)
            val_saldo = valor_base - val_adianta
            # -------------------------------------

            for i in range(janela_meses):
                data_ref = hoje + relativedelta(months=i)
                
                # Gera as duas datas ajustadas (ex: Fev dia 30 vira dia 28)
                venc1 = get_data_segura(data_ref.year, data_ref.month, dia1)
                venc2 = get_data_segura(data_ref.year, data_ref.month, dia2)
                
                # Adiciona Adiantamento
                if venc1 > hoje and venc1 not in datas_cobertas:
                    lista_novos.append((venc1, val_adianta, f"Adiantamento ({perc}%)"))
                
                # Adiciona Saldo
                if venc2 > hoje and venc2 not in datas_cobertas:
                    lista_novos.append((venc2, val_saldo, "Saldo Salário"))

        elif colaborador.frequencia_pagamento == 'semanal':
            try: dia_semana = int(colaborador.dia_pagamento)
            except: dia_semana = 4 
            
            val_semana = valor_base / 4 # Simplificado
            cursor = hoje
            while cursor.weekday() != dia_semana: cursor += timedelta(days=1)
            
            for _ in range(24):
                cursor += timedelta(weeks=1)
                if cursor not in datas_cobertas:
                    lista_novos.append((cursor, val_semana, "Pgto Semanal"))

        # 3. SALVAR
        for dt, val, desc in lista_novos:
            nova = Despesa(
                descricao=f"{desc} - {colaborador.nome_completo}",
                valor=val,
                categoria="pessoal",
                tipo_custo="fixo",
                data_competencia=dt.replace(day=1),
                data_vencimento=dt,
                status="pendente",
                forma_pagamento="pix" if colaborador.chave_pix else "transferencia",
                colaborador_id=colaborador.id,
                usuario_id=current_user.id,
                origem='rh_automatico',
                observacao=f"Pix: {colaborador.chave_pix or 'N/D'}"
            )
            db.session.add(nova)
            novos += 1

        return f"Sincronizado: {novos} lançamentos."
    except Exception as e:
        print(f"Erro Sync: {e}")
        return "Erro ao gerar."

# --- ROTAS DE COLABORADORES ---

@bp_rh.route('/', methods=['GET'])
@login_required
@cargo_exigido('rh_equipe')
def listar_colaboradores():
    colaboradores = Colaborador.query.order_by(Colaborador.ativo.desc(), Colaborador.nome_completo).all()
    return render_template('rh/lista_colaboradores.html', colaboradores=colaboradores)

@bp_rh.route('/novo', methods=['GET', 'POST'])
@login_required
@cargo_exigido('rh_equipe')
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
                
                # Campos Financeiros
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
            
            # Sync Financeiro
            msg_sync = ""
            if form.gerar_financeiro.data and form.salario_base.data:
                msg_sync = sincronizar_financeiro_rh(novo)
            
            db.session.commit()
            flash(f'Colaborador cadastrado! {msg_sync}', 'success')
            return redirect(url_for('rh.listar_colaboradores'))

    return render_template('rh/cadastro_colaborador.html', form=form, titulo="Novo Colaborador")

@bp_rh.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
@cargo_exigido('rh_equipe')
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
            
            # Sync Financeiro
            if form.gerar_financeiro.data:
                msg_sync = sincronizar_financeiro_rh(colab)
                flash(f'Dados atualizados. {msg_sync}', 'success')
            else:
                flash('Dados atualizados.', 'success')
                
            db.session.commit()
            return redirect(url_for('rh.listar_colaboradores'))

    return render_template('rh/cadastro_colaborador.html', form=form, titulo="Editar Colaborador", editando=True)

@bp_rh.route('/perfil/<int:id>')
@login_required
@cargo_exigido('rh_equipe')
def perfil_colaborador(id):
    colab = Colaborador.query.get_or_404(id)
    return render_template('rh/perfil_colaborador.html', colab=colab)