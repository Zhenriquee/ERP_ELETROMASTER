from flask import redirect, url_for, flash, request, jsonify, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from src.extensoes import banco_de_dados as db
from src.modulos.vendas.modelos import Venda,  hora_brasilia, ItemVenda, ItemVendaHistorico, FotoItemVenda
from src.modulos.autenticacao.permissoes import cargo_exigido  # <--- IMPORTAR
from io import BytesIO # Necessário para converter bytes em arquivo
from . import bp_vendas

@bp_vendas.route('/servicos/<int:id>/status/<novo_status>')
@login_required
@cargo_exigido('vendas_operar')  # <--- PROTEÇÃO APLICADA
def mudar_status(id, novo_status):
    venda = Venda.query.get_or_404(id)
    agora = hora_brasilia()
    mapa_status = {'producao': 'Em Produção', 'pronto': 'Pronto', 'entregue': 'Entregue'}
    
    if novo_status in mapa_status:
        venda.status = novo_status
        if novo_status == 'producao':
            venda.data_inicio_producao = agora
            venda.usuario_producao_id = current_user.id
        elif novo_status == 'pronto':
            venda.data_pronto = agora
            venda.usuario_pronto_id = current_user.id
        elif novo_status == 'entregue':
            venda.data_entrega = agora
            venda.usuario_entrega_id = current_user.id

        if venda.modo == 'multipla':
            for item in venda.itens:
                if item.status != novo_status:
                    status_antigo = item.status
                    item.status = novo_status
                    if novo_status == 'producao':
                        item.data_inicio_producao = agora
                        item.usuario_producao_id = current_user.id
                    elif novo_status == 'pronto':
                        item.data_pronto = agora
                        item.usuario_pronto_id = current_user.id
                    elif novo_status == 'entregue':
                        item.data_entregue = agora
                        item.usuario_entrega_id = current_user.id
                    
                    log = ItemVendaHistorico(
                        item_id=item.id,
                        usuario_id=current_user.id,
                        status_anterior=status_antigo,
                        status_novo=novo_status,
                        acao=f"Ação em Massa ({mapa_status[novo_status]})",
                        data_acao=agora
                    )
                    db.session.add(log)

        db.session.commit()
        flash(f'Status atualizado para: {mapa_status[novo_status]}', 'success')
    
    return redirect(url_for('vendas.listar_vendas'))

@bp_vendas.route('/itens/<int:id>/status/<novo_status>')
@login_required
@cargo_exigido('vendas_operar')  # <--- PROTEÇÃO APLICADA
def mudar_status_item(id, novo_status):
    item = ItemVenda.query.get_or_404(id)
    venda_pai = Venda.query.get(item.venda_id)
    agora = hora_brasilia()
    
    mapa_status = {'pendente': 'Pendente', 'producao': 'Em Produção', 'pronto': 'Pronto', 'entregue': 'Entregue'}
    
    if novo_status in mapa_status:
        item.status = novo_status
        if novo_status == 'producao':
            item.data_inicio_producao = agora
            item.usuario_producao_id = current_user.id
        elif novo_status == 'pronto':
            item.data_pronto = agora
            item.usuario_pronto_id = current_user.id
        elif novo_status == 'entregue':
            item.data_entregue = agora
            item.usuario_entrega_id = current_user.id
            
        todos_itens = ItemVenda.query.filter_by(venda_id=venda_pai.id).all()
        status_set = set(i.status for i in todos_itens)
        
        if status_set == {'entregue'}:
            if venda_pai.status != 'entregue':
                venda_pai.status = 'entregue'
                venda_pai.data_entrega = agora
                venda_pai.usuario_entrega_id = current_user.id
        elif all(s in ['pronto', 'entregue'] for s in status_set):
            if venda_pai.status != 'pronto':
                venda_pai.status = 'pronto'
                venda_pai.data_pronto = agora
                venda_pai.usuario_pronto_id = current_user.id
        elif 'producao' in status_set or 'pronto' in status_set or 'entregue' in status_set:
            if venda_pai.status == 'pendente':
                venda_pai.status = 'producao'
                venda_pai.data_inicio_producao = agora
                venda_pai.usuario_producao_id = current_user.id

        db.session.commit()
        flash(f'Item atualizado.', 'success')
    
    return redirect(url_for('vendas.listar_vendas'))

@bp_vendas.route('/servicos/<int:id>/cancelar', methods=['POST'])
@login_required
@cargo_exigido('gestao_cancelar')  # <--- PROTEÇÃO APLICADA
def cancelar_venda(id):
    venda = Venda.query.get_or_404(id)
    if venda.status == 'entregue' and venda.valor_restante <= 0.01:
        flash('Não é possível cancelar um serviço finalizado e pago.', 'error')
        return redirect(url_for('vendas.listar_vendas'))
        
    motivo = request.form.get('motivo_cancelamento')
    if not motivo or len(motivo.strip()) < 5:
        flash('Informe o motivo (min 5 chars).', 'error')
        return redirect(url_for('vendas.listar_vendas'))
    
    venda.status = 'cancelado'
    venda.motivo_cancelamento = motivo
    venda.data_cancelamento = hora_brasilia()
    venda.usuario_cancelamento_id = current_user.id
    
    db.session.commit()
    flash('Serviço cancelado.', 'info')
    
    return redirect(url_for('vendas.listar_vendas'))


# --- ROTA PARA SERVIR IMAGEM DO BANCO ---
@bp_vendas.route('/imagem/<int:foto_id>')
@login_required
def imagem_db(foto_id):
    foto = FotoItemVenda.query.get_or_404(foto_id)
    
    return send_file(
        BytesIO(foto.dados_binarios),
        mimetype=foto.tipo_mime,
        as_attachment=False,
        download_name=foto.nome_arquivo
    )
# -----------------------------------------

# --- UPLOAD DE FOTO (MODAL) ---
@bp_vendas.route('/servicos/<int:id>/upload-foto', methods=['POST'])
@login_required
@cargo_exigido('gestao_editar')
def upload_foto_servico(id):
    venda = Venda.query.get_or_404(id)
    arquivo = request.files.get('foto')
    
    if not arquivo:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400
        
    try:
        # Vincula ao primeiro item da venda
        item_alvo = venda.itens[0] if venda.itens else None
        if not item_alvo:
             return jsonify({'erro': 'Venda sem itens para vincular foto'}), 400

        filename = secure_filename(arquivo.filename)
        mimetype = arquivo.mimetype or 'application/octet-stream'
        dados = arquivo.read() # Lê o arquivo para memória
        
        # Salva no banco
        nova_foto = FotoItemVenda(
            item_venda_id=item_alvo.id,
            nome_arquivo=filename,
            tipo_mime=mimetype,
            dados_binarios=dados,
            etapa='gestao',
            enviado_por_id=current_user.id
        )
        db.session.add(nova_foto)
        db.session.commit()
        
        return jsonify({
            'sucesso': True, 
            'url': url_for('vendas.imagem_db', foto_id=nova_foto.id)
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

# --- DELETAR FOTO ---
@bp_vendas.route('/fotos/<int:foto_id>/deletar', methods=['POST'])
@login_required
@cargo_exigido('gestao_editar')
def deletar_foto(foto_id):
    foto = FotoItemVenda.query.get_or_404(foto_id)
    try:
        db.session.delete(foto)
        db.session.commit()
        return jsonify({'sucesso': True})
    except Exception as e:
        return jsonify({'erro': str(e)}), 500
    
@bp_vendas.route('/itens/<int:item_id>/upload-foto', methods=['POST'])
@login_required
@cargo_exigido('gestao_editar')
def upload_foto_item_especifico(item_id):
    item = ItemVenda.query.get_or_404(item_id)
    arquivo = request.files.get('foto')
    
    if not arquivo:
        return jsonify({'erro': 'Nenhum arquivo enviado'}), 400
        
    try:
        filename = secure_filename(arquivo.filename)
        mimetype = arquivo.mimetype or 'application/octet-stream'
        dados = arquivo.read()
        
        nova_foto = FotoItemVenda(
            item_venda_id=item.id, # Vincula direto ao item correto
            nome_arquivo=filename,
            tipo_mime=mimetype,
            dados_binarios=dados,
            etapa='gestao_extra',
            enviado_por_id=current_user.id
        )
        db.session.add(nova_foto)
        db.session.commit()
        
        return jsonify({
            'sucesso': True, 
            'url': url_for('vendas.imagem_db', foto_id=nova_foto.id)
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500    