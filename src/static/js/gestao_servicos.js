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
            const vendaId = d.id; // ID da venda para usar nas fotos
            
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

            // Botões de Ação (Status)
            gerarBotoesStatus(d.id, d.status);

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

            if(formCancelar) formCancelar.action = `/vendas/servicos/${d.id}/cancelar`;
            
            // --- NOVO: Carregar Detalhes Técnicos e Fotos ---
            if(typeof carregarDetalhesTecnicos === 'function') {
                carregarDetalhesTecnicos(vendaId);
            }

            // --- NOVO: Configurar Input de Upload ---
            const inputFoto = document.getElementById('inputNovaFoto');
            if(inputFoto) {
                // Clona o input para remover listeners antigos e evitar duplicação de eventos
                const novoInput = inputFoto.cloneNode(true);
                inputFoto.parentNode.replaceChild(novoInput, inputFoto);
                
                novoInput.addEventListener('change', function() {
                    if (this.files && this.files[0]) {
                        uploadFoto(vendaId, this.files[0]);
                    }
                });
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

    function gerarBotoesStatus(id, status) {
        let html = '';
        const btnBase = "w-full py-3 rounded-lg font-bold text-white shadow-md hover:shadow-lg transition-all flex items-center justify-center";
        
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
// FUNÇÕES GLOBAIS (FORA DO DOMContentLoaded PARA SEREM ACESSÍVEIS)
// =========================================================================

// Carrega os dados da Aba Técnico & Arquivos
window.carregarDetalhesTecnicos = async function(id) {
    const container = document.getElementById('detalhesTecnicosContainer');
    const galeria = document.getElementById('galeriaFotos');
    const vazio = document.getElementById('msgSemFotos');
    
    if(container) container.innerHTML = '<p class="text-gray-400 text-xs animate-pulse">Carregando dados...</p>';
    
    try {
        const res = await fetch(`/vendas/api/servico/${id}/detalhes`);
        const data = await res.json();
        
        // 1. Renderiza Dados Técnicos
        let htmlTec = '';
        if (data.modo === 'simples') {
            htmlTec += `<div><span class="block text-xs text-gray-400 uppercase">Medidas</span><span class="font-bold text-navy-900">${data.dimensao_1} x ${data.dimensao_2}</span></div>`;
            htmlTec += `<div><span class="block text-xs text-gray-400 uppercase">Tipo</span><span class="font-bold text-navy-900">${data.tipo_medida}</span></div>`;
        }
        
        // Lista Itens com material e quantidade
        data.itens.forEach((item) => {
            htmlTec += `<div class="col-span-2 border-t border-gray-100 pt-2 mt-2">
                <p class="font-bold text-navy-900">${item.descricao}</p>
                <p class="text-xs text-gray-500">${item.material} • ${item.qtd} un</p>
            </div>`;
        });
        
        if(container) container.innerHTML = htmlTec;

        // 2. Renderiza Galeria de Fotos
        if(galeria) {
            galeria.innerHTML = '';
            if (data.fotos && data.fotos.length > 0) {
                if(vazio) vazio.classList.add('hidden');
                
                data.fotos.forEach(f => {
                    const div = document.createElement('div');
                    div.className = "relative group rounded-lg overflow-hidden border border-gray-200 aspect-square bg-gray-100";
                    div.innerHTML = `
                        <img src="${f.url}" class="w-full h-full object-cover cursor-pointer transition-transform hover:scale-110" onclick="window.open('${f.url}', '_blank')">
                        <button onclick="deletarFoto('${f.id}', '${id}')" class="absolute top-1 right-1 bg-red-500 text-white p-1 rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600 shadow-sm" title="Excluir">
                            <i data-lucide="trash-2" class="w-3 h-3"></i>
                        </button>
                    `;
                    galeria.appendChild(div);
                });
            } else {
                if(vazio) vazio.classList.remove('hidden');
            }
        }
        
        if(typeof lucide !== 'undefined') lucide.createIcons();

    } catch (error) {
        console.error(error);
        if(container) container.innerHTML = '<p class="text-red-500 text-xs">Erro ao carregar detalhes.</p>';
    }
};

// Envia a foto para o servidor
window.uploadFoto = async function(vendaId, file) {
    const formData = new FormData();
    formData.append('foto', file);
    
    const btnLabel = document.querySelector('label[for="inputNovaFoto"]');
    const originalText = btnLabel ? btnLabel.innerHTML : 'Nova Foto';
    
    // Mostra loading no botão
    if(btnLabel) btnLabel.innerHTML = '<i data-lucide="loader-2" class="w-3 h-3 mr-1 animate-spin"></i> ...';
    if(typeof lucide !== 'undefined') lucide.createIcons();

    try {
        const res = await fetch(`/vendas/servicos/${vendaId}/upload-foto`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        
        if (data.sucesso) {
            // Sucesso: Recarrega a lista de fotos
            carregarDetalhesTecnicos(vendaId);
        } else {
            alert('Erro: ' + data.erro);
        }
    } catch (e) {
        alert('Erro no upload.');
        console.error(e);
    } finally {
        // Restaura o botão original
        if(btnLabel) btnLabel.innerHTML = originalText;
        if(typeof lucide !== 'undefined') lucide.createIcons();
    }
};

// Deleta foto (função chamada pelo botão de lixeira nas fotos)
window.deletarFoto = async function(fotoId, vendaId) {
    if(!confirm('Excluir esta imagem?')) return;
    
    try {
        const res = await fetch(`/vendas/fotos/${fotoId}/deletar`, { method: 'POST' });
        if (res.ok) {
            carregarDetalhesTecnicos(vendaId);
        } else {
            alert('Erro ao excluir.');
        }
    } catch(e) { console.error(e); }
};