from flask import render_template, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from io import BytesIO

from src.extensoes import banco_de_dados as db
from src.modulos.autenticacao.permissoes import cargo_exigido
from src.modulos.rh import bp_rh

# Modelos
from src.modulos.rh.modelos import Colaborador, DocumentoColaborador
# Formulários
from src.modulos.rh.formularios import FormularioDocumentoRH

@bp_rh.route('/documentos/<int:colaborador_id>', methods=['GET', 'POST'])
@login_required
@cargo_exigido('rh_equipe')
def documentos_colaborador(colaborador_id):
    colab = Colaborador.query.get_or_404(colaborador_id)
    form = FormularioDocumentoRH()
    
    if form.validate_on_submit():
        arquivo = form.arquivo.data
        filename = secure_filename(arquivo.filename)
        dados = arquivo.read()
        
        novo_doc = DocumentoColaborador(
            colaborador_id=colab.id,
            nome_original=filename,
            tipo_arquivo=filename.rsplit('.', 1)[1].lower() if '.' in filename else 'bin',
            tamanho_kb=len(dados)/1024,
            dados_binarios=dados,
            descricao=form.descricao.data,
            enviado_por_id=current_user.id
        )
        db.session.add(novo_doc)
        db.session.commit()
        flash('Documento anexado.', 'success')
        return redirect(url_for('rh.documentos_colaborador', colaborador_id=colab.id))
        
    return render_template('rh/documentos.html', colab=colab, form=form)

@bp_rh.route('/documentos/visualizar/<int:doc_id>')
@login_required
def visualizar_documento_rh(doc_id):
    doc = DocumentoColaborador.query.get_or_404(doc_id)
    
    if not current_user.tem_permissao('rh_equipe'):
        return "Acesso Negado", 403
        
    # Define mimetype correto
    tipo_mime = 'application/pdf' if doc.tipo_arquivo == 'pdf' else f'image/{doc.tipo_arquivo}'
    if doc.tipo_arquivo == 'jpg': tipo_mime = 'image/jpeg'

    return send_file(
        BytesIO(doc.dados_binarios),
        mimetype=tipo_mime,
        as_attachment=False,
        download_name=doc.nome_original
    )

@bp_rh.route('/documentos/baixar/<int:doc_id>')
@login_required
def baixar_documento_rh(doc_id):
    doc = DocumentoColaborador.query.get_or_404(doc_id)
    
    if not current_user.tem_permissao('rh_equipe'):
        return "Acesso Negado", 403
        
    return send_file(
        BytesIO(doc.dados_binarios),
        download_name=doc.nome_original,
        as_attachment=True
    )

@bp_rh.route('/documentos/deletar/<int:doc_id>')
@login_required
@cargo_exigido('rh_equipe')
def deletar_documento_rh(doc_id):
    doc = DocumentoColaborador.query.get_or_404(doc_id)
    colab_id = doc.colaborador_id
    db.session.delete(doc)
    db.session.commit()
    flash('Documento removido.', 'success')
    return redirect(url_for('rh.documentos_colaborador', colaborador_id=colab_id))