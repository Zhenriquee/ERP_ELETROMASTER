document.addEventListener('DOMContentLoaded', function() {
    
    if(typeof lucide !== 'undefined') lucide.createIcons();

    // 1. FORMATAÇÃO MONETÁRIA BRASILEIRA
    const formatarDinheiro = () => {
        document.querySelectorAll('.format-money').forEach(el => {
            const valorOriginal = parseFloat(el.dataset.value);
            if (!isNaN(valorOriginal)) {
                el.innerText = valorOriginal.toLocaleString('pt-BR', {
                    style: 'currency',
                    currency: 'BRL'
                });
            }
        });
    };
    formatarDinheiro();

    // 2. Filtros e Busca
    const inpTexto = document.getElementById('filtroTexto');
    const selStatus = document.getElementById('filtroStatus');
    const selVendedor = document.getElementById('filtroVendedor');
    const inpData = document.getElementById('filtroData');

    function aplicarFiltros() {
        const q = inpTexto ? inpTexto.value : '';
        const status = selStatus ? selStatus.value : '';
        const vendedor = selVendedor ? selVendedor.value : '';
        const data = inpData ? inpData.value : '';

        const params = new URLSearchParams();
        if(q) params.append('q', q);
        if(status) params.append('status', status);
        if(vendedor) params.append('vendedor', vendedor);
        if(data) params.append('data', data);
        params.append('page', 1);

        window.location.href = `${window.location.pathname}?${params.toString()}`;
    }

    if(selStatus) selStatus.addEventListener('change', aplicarFiltros);
    if(selVendedor) selVendedor.addEventListener('change', aplicarFiltros);
    if(inpData) inpData.addEventListener('change', aplicarFiltros);
    
    if(inpTexto) {
        let timeout;
        inpTexto.addEventListener('input', () => {
            clearTimeout(timeout);
            timeout = setTimeout(aplicarFiltros, 800);
        });
        inpTexto.addEventListener('keypress', (e) => { if (e.key === 'Enter') aplicarFiltros(); });
    }

    // 3. LÓGICA DO MODAL
    const modal = document.getElementById('modalServico');
    const btnFechar = document.getElementById('btnFecharModal');
    const overlay = document.getElementById('modalOverlay');
    const tabs = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    const btnWhatsapp = document.getElementById('btnWhatsapp');
    const formPagamento = document.getElementById('formPagamento');
    const formCancelar = document.getElementById('formCancelar');
    const timelineContainer = document.getElementById('timelineContainer');
    const botoesStatus = document.getElementById('botoesStatus');
    const areaPagamento = document.getElementById('areaPagamento');
    const msgPago = document.getElementById('msgPago');
    
    // Controle de Abas
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => {
                t.classList.remove('active', 'text-navy-900', 'border-navy-900');
                t.classList.add('text-gray-500', 'border-transparent');
                const i = t.querySelector('i');
                if(i) i.classList.remove('text-electric-500');
            });
            tabContents.forEach(c => {
                c.classList.remove('active');
                c.classList.add('hidden');
            });

            tab.classList.add('active', 'text-navy-900', 'border-navy-900');
            tab.classList.remove('text-gray-500', 'border-transparent');
            const i = tab.querySelector('i');
            if(i) i.classList.add('text-electric-500');

            const target = document.getElementById(tab.dataset.target);
            if(target) {
                target.classList.remove('hidden');
                target.classList.add('active');
            }
        });
    });

    // Abrir Modal
    const btnsAbrir = document.querySelectorAll('.btn-abrir-modal');
    btnsAbrir.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const d = this.dataset;
            const vendaId = d.id; 
            
            // Preenche dados básicos
            document.getElementById('modalTitulo').innerText = `Serviço #${d.id} - ${d.cliente}`;
            document.getElementById('modalDescricao').innerText = d.descricao;
            document.getElementById('modalContato').innerText = d.contato || '--';
            
            // Botão WhatsApp
            if(d.contato) {
                const num = d.contato.replace(/\D/g, '');
                if(num.length >= 10) {
                    btnWhatsapp.href = `https://wa.me/55${num}`;
                    btnWhatsapp.classList.remove('hidden');
                } else { btnWhatsapp.classList.add('hidden'); }
            } else { btnWhatsapp.classList.add('hidden'); }

            // Histórico e Timeline
            try {
                const hist = JSON.parse(d.historico);
                document.getElementById('modalVendedor').innerText = hist.vendedor || '--';
                document.getElementById('modalDataVenda').innerText = formatarData(hist.criado_em);
                montarTimeline(hist);
            } catch(e) { console.error('Erro historico', e); }

            // Botões de Ação (Status) - AGORA RECEBE A PERMISSÃO
            gerarBotoesStatus(d.id, d.status, d.podeStatus === 'true');

            // Aba Financeira
            if(document.getElementById('modalRestanteDisplay')) {
                const restante = parseFloat(d.restante);
                document.getElementById('modalRestanteDisplay').innerText = restante.toLocaleString('pt-BR', {minimumFractionDigits: 2});
                
                if(formPagamento) formPagamento.action = `/vendas/servicos/${d.id}/pagamento`;
                
                if(restante <= 0.01) {
                    if(areaPagamento) areaPagamento.classList.add('hidden');
                    if(msgPago) msgPago.classList.remove('hidden');
                } else {
                    if(areaPagamento) areaPagamento.classList.remove('hidden');
                    if(msgPago) msgPago.classList.add('hidden');
                    
                    const radioParcial = document.querySelector('input[name="tipo_recebimento"][value="parcial"]');
                    if(radioParcial) radioParcial.click();
                    
                    const dtHoje = new Date().toISOString().split('T')[0];
                    const inpDt = document.querySelector('input[name="data_pagamento"]');
                    if(inpDt) inpDt.value = dtHoje;
                }
            }

            // Ação de Cancelar
            if(formCancelar) formCancelar.action = `/vendas/servicos/${d.id}/cancelar`;
            const btnShowCancelar = document.getElementById('btnShowCancelar');
            if (btnShowCancelar) {
                if (d.podeCancelar === 'true' && d.status !== 'cancelado' && d.status !== 'entregue') {
                    btnShowCancelar.classList.remove('hidden');
                } else {
                    btnShowCancelar.classList.add('hidden');
                }
            }
            
            // Carregar Detalhes Técnicos e Fotos
            if(typeof carregarDetalhesTecnicos === 'function') {
                carregarDetalhesTecnicos(vendaId);
            }

            // Reseta para a primeira aba e mostra modal
            if(tabs.length > 0) tabs[0].click();
            modal.classList.remove('hidden');
        });
    });

    // Funções Auxiliares do Modal
    function formatarData(dataStr) {
        if(!dataStr) return '--';
        if(dataStr.includes('T') || dataStr.includes(' ')) {
            const date = new Date(dataStr);
            return date.toLocaleDateString('pt-BR') + ' ' + date.toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'});
        }
        return dataStr;
    }

    function montarTimeline(hist) {
        let html = '';
        html += itemTimeline('Solicitação Criada', hist.criado_em, true);
        const temProducao = !!hist.data_producao;
        html += itemTimeline('Início Produção', hist.data_producao, temProducao);
        const temPronto = !!hist.data_pronto;
        html += itemTimeline('Pronto p/ Retirada', hist.data_pronto, temPronto);
        const temEntrega = !!hist.data_entrega;
        html += itemTimeline('Entregue ao Cliente', hist.data_entrega, temEntrega);

        if(hist.data_cancelamento) {
            html += `<div class="timeline-item">
                <div class="timeline-dot danger"></div>
                <p class="text-sm font-bold text-red-600">Cancelado</p>
                <div class="text-xs text-gray-500">${formatarData(hist.data_cancelamento)}</div>
                <p class="text-xs text-red-500 mt-1 italic">"${hist.motivo_cancelamento}"</p>
            </div>`;
        }
        timelineContainer.innerHTML = html;
    }

    function itemTimeline(titulo, data, ativo) {
        return `
        <div class="timeline-item">
            <div class="timeline-dot ${ativo ? 'active' : ''}"></div>
            <p class="text-sm font-bold ${ativo ? 'text-navy-900' : 'text-gray-400'}">${titulo}</p>
            <div class="text-xs text-gray-500">${formatarData(data)}</div>
        </div>`;
    }

    // AGORA RECEBE A PERMISSÃO E TRAVA SE NECESSÁRIO
    function gerarBotoesStatus(id, status, podeStatus) {
        let html = '';
        const btnBase = "w-full py-3 rounded-lg font-bold text-white shadow-md hover:shadow-lg transition-all flex items-center justify-center";
        
        // Bloqueio Visual se não tiver permissão para mudar status
        if (!podeStatus && status !== 'cancelado' && status !== 'entregue') {
            html = `<div class="p-3 bg-gray-100 text-gray-500 rounded text-center text-sm font-bold uppercase border border-gray-200"><i data-lucide="lock" class="w-4 h-4 inline mr-2"></i> Status Atual: ${status}</div>`;
            botoesStatus.innerHTML = html;
            if(typeof lucide !== 'undefined') lucide.createIcons();
            return;
        }

        if(status === 'pendente') {
            html = `<div class="p-3 bg-gray-100 text-gray-500 rounded text-center text-sm">Aguardando início na Produção</div>`;
        } else if (status === 'producao') {
            html = `<div class="p-3 bg-blue-50 text-blue-600 rounded text-center text-sm font-bold animate-pulse">Em Produção...</div>`;
        } else if (status === 'pronto') {
            html = `<a href="/vendas/servicos/${id}/status/entregue" class="${btnBase} bg-green-600 hover:bg-green-700">
                <i data-lucide="truck" class="w-5 h-5 mr-2"></i> Confirmar Entrega
            </a>`;
        } else if (status === 'entregue') {
            html = `<div class="p-3 bg-green-50 text-green-700 rounded text-center text-sm font-bold">Serviço Finalizado</div>`;
        } else if (status === 'cancelado') {
            html = `<div class="p-3 bg-red-50 text-red-600 rounded text-center text-sm font-bold">Cancelado</div>`;
        }
        botoesStatus.innerHTML = html;
        if(typeof lucide !== 'undefined') lucide.createIcons();
    }

    const btnShowCancelar = document.getElementById('btnShowCancelar');
    const areaCancelamento = document.getElementById('areaCancelamento');
    const btnAbortarCancelamento = document.getElementById('btnAbortarCancelamento');
    const divStatusActions = document.getElementById('divStatusActions');

    if(btnShowCancelar) {
        btnShowCancelar.addEventListener('click', () => {
            divStatusActions.classList.add('hidden');
            areaCancelamento.classList.remove('hidden');
        });
    }
    if(btnAbortarCancelamento) {
        btnAbortarCancelamento.addEventListener('click', () => {
            areaCancelamento.classList.add('hidden');
            divStatusActions.classList.remove('hidden');
        });
    }

    const radiosPgto = document.querySelectorAll('input[name="tipo_recebimento"]');
    const divValor = document.getElementById('divValorInput');
    const inputValor = document.querySelector('input[name="valor"]');

    function toggleInputValor() {
        if(!divValor || !inputValor) return;
        const tipo = document.querySelector('input[name="tipo_recebimento"]:checked').value;
        if(tipo === 'total') {
            divValor.classList.add('opacity-50', 'pointer-events-none');
            inputValor.required = false;
            inputValor.value = '';
        } else {
            divValor.classList.remove('opacity-50', 'pointer-events-none');
            inputValor.required = true;
        }
    }
    radiosPgto.forEach(r => r.addEventListener('change', toggleInputValor));

    function fechar() { modal.classList.add('hidden'); }
    if(btnFechar) btnFechar.addEventListener('click', fechar);
    if(overlay) overlay.addEventListener('click', fechar);
});

// =========================================================================
// FUNÇÕES GLOBAIS DE FOTOS E DETALHES TÉCNICOS
// =========================================================================

window.carregarDetalhesTecnicos = async function(vendaId) {
    const container = document.getElementById('containerItensTecnicos');
    if (!container) return;
    
    container.innerHTML = '<div class="flex justify-center py-10 text-blue-500"><i data-lucide="loader-2" class="w-8 h-8 animate-spin"></i></div>';
    if(typeof lucide !== 'undefined') lucide.createIcons();

    try {
        const res = await fetch(`/vendas/api/servico/${vendaId}/detalhes`);
        const data = await res.json();
        
        container.innerHTML = ''; // Limpa loading

        if (!data.itens || data.itens.length === 0) {
            container.innerHTML = '<p class="text-center text-gray-400">Nenhum item encontrado.</p>';
            return;
        }

        // GERA UMA SEÇÃO PARA CADA ITEM
        data.itens.forEach((item, index) => {
            
            // Resgata o botão que foi clicado lá na tabela para saber se ESTE usuário tem permissão de fotos
            const btnAtivo = document.querySelector(`.btn-abrir-modal[data-id="${vendaId}"]`);
            const podeFotos = btnAtivo && btnAtivo.dataset.podeFotos === 'true';
            
            // 1. HTML das Fotos
            let htmlFotos = '';
            if (item.fotos && item.fotos.length > 0) {
                item.fotos.forEach(f => {
                    // Lixeira só aparece se tiver permissão
                    let btnExcluir = podeFotos ? `
                        <button onclick="deletarFoto('${f.id}', '${vendaId}')" class="absolute top-1 right-1 bg-red-500 text-white p-1.5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600 shadow-sm" title="Excluir Imagem">
                            <i data-lucide="trash-2" class="w-4 h-4"></i>
                        </button>` : '';

                    htmlFotos += `
                        <div class="relative group rounded-lg overflow-hidden border border-gray-200 aspect-square bg-gray-50">
                            <img src="${f.url}" class="w-full h-full object-cover cursor-pointer transition-transform hover:scale-110" onclick="window.open('${f.url}', '_blank')">
                            ${btnExcluir}
                        </div>`;
                });
            } else {
                htmlFotos = `<div class="col-span-full py-4 text-center text-gray-400 text-xs italic border border-dashed border-gray-200 rounded-lg">Sem fotos para este item.</div>`;
            }

            // Botão de Add Foto só aparece se tiver permissão
            let btnAddFoto = podeFotos ? `
                <label class="cursor-pointer bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-bold px-3 py-1.5 rounded-lg flex items-center transition-colors border border-blue-200">
                    <i data-lucide="upload" class="w-3 h-3 mr-1.5"></i> Add Foto
                    <input type="file" class="hidden" accept="image/*" onchange="uploadFotoItem('${item.id}', '${vendaId}', this)">
                </label>` : '';

            // 2. Monta o Card do Item Completo
            const itemHtml = `
                <div class="bg-white p-5 rounded-xl border border-gray-200 shadow-sm mb-4">
                    <div class="flex justify-between items-start mb-4 border-b border-gray-100 pb-3">
                        <div>
                            <h4 class="font-bold text-navy-900 text-lg flex items-center">
                                <span class="bg-navy-50 text-navy-800 text-xs px-2 py-1 rounded mr-2">Item ${index + 1}</span>
                                ${item.descricao}
                            </h4>
                            <p class="text-sm text-gray-500 mt-1">
                                ${item.material} • <span class="font-bold text-navy-700">${item.qtd} un</span> 
                                ${data.modo === 'simples' ? ` • ${item.medidas}` : ''}
                            </p>
                        </div>
                    </div>

                    <div>
                        <div class="flex justify-between items-center mb-3">
                            <p class="text-xs font-bold text-gray-400 uppercase">Arquivos & Imagens</p>
                            ${btnAddFoto}
                        </div>
                        <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-3">
                            ${htmlFotos}
                        </div>
                    </div>
                </div>
            `;
            
            container.insertAdjacentHTML('beforeend', itemHtml);
        });

        if(typeof lucide !== 'undefined') lucide.createIcons();

    } catch (error) {
        console.error(error);
        container.innerHTML = '<div class="p-4 bg-red-50 text-red-600 rounded text-center text-sm">Erro ao carregar itens.</div>';
    }
};

window.uploadFotoItem = async function(itemId, vendaId, input) {
    if (!input.files || !input.files[0]) return;
    
    const file = input.files[0];
    const formData = new FormData();
    formData.append('foto', file);
    
    const labelBtn = input.parentElement;
    const textoOriginal = labelBtn.innerHTML;
    labelBtn.innerHTML = '<i data-lucide="loader-2" class="w-3 h-3 mr-1 animate-spin"></i> Enviando...';
    if(typeof lucide !== 'undefined') lucide.createIcons();
    
    try {
        const res = await fetch(`/vendas/itens/${itemId}/upload-foto`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        
        if (data.sucesso) {
            carregarDetalhesTecnicos(vendaId);
        } else {
            alert('Erro: ' + data.erro);
            labelBtn.innerHTML = textoOriginal; 
            if(typeof lucide !== 'undefined') lucide.createIcons();
        }
    } catch (e) {
        alert('Erro de conexão no upload.');
        labelBtn.innerHTML = textoOriginal;
        if(typeof lucide !== 'undefined') lucide.createIcons();
    }
};

window.deletarFoto = async function(fotoId, vendaId) {
    if(!confirm('Excluir esta imagem permanentemente?')) return;
    try {
        const res = await fetch(`/vendas/fotos/${fotoId}/deletar`, { method: 'POST' });
        if (res.ok) {
            carregarDetalhesTecnicos(vendaId);
        } else {
            alert('Erro ao excluir.');
        }
    } catch(e) { console.error(e); }
};