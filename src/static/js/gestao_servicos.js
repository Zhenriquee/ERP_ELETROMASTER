document.addEventListener('DOMContentLoaded', function() {
    
    // ==========================================
    // 1. SELEÇÃO DE ELEMENTOS DO DOM
    // ==========================================
    
    // Modal e Overlay
    const modal = document.getElementById('modalServico');
    const overlay = document.getElementById('modalOverlay');
    const btnFechar = document.getElementById('btnFecharModal');
    
    // Seções internas do Modal
    const divStatusActions = document.getElementById('divStatusActions');
    const areaPagamento = document.getElementById('areaPagamento');
    const areaCancelamento = document.getElementById('areaCancelamento');
    const msgPago = document.getElementById('msgPago');
    const botoesStatus = document.getElementById('botoesStatus');
    const timelineContainer = document.getElementById('timelineContainer');
    
    // --- NOVO: Seção de Itens Individuais ---
    const containerItens = document.getElementById('containerItens');
    const tabelaItensModal = document.getElementById('tabelaItensModal');
    
    // Formulários
    const formPagamento = document.getElementById('formPagamento');
    const formCancelar = document.getElementById('formCancelar');

    // Botões Especiais
    const btnShowCancelar = document.getElementById('btnShowCancelar');
    const btnAbortarCancelamento = document.getElementById('btnAbortarCancelamento');
    const btnWhatsapp = document.getElementById('btnWhatsapp');

    // Filtros
    const filtroTexto = document.getElementById('filtroTexto');
    const filtroStatus = document.getElementById('filtroStatus');
    const filtroVendedor = document.getElementById('filtroVendedor');
    const filtroData = document.getElementById('filtroData');
    const tabela = document.getElementById('tabelaServicos');

    // Radios de Pagamento
    const radiosTipo = document.querySelectorAll('input[name="tipo_recebimento"]');


    // ============================================================
    // 2. FILTROS AVANÇADOS
    // ============================================================
    function filtrarTabelaCompleta() {
        if(!tabela) return; // Segurança

        const texto = filtroTexto.value.toLowerCase();
        const status = filtroStatus.value.toLowerCase();
        const vendedor = filtroVendedor.value;
        const data = filtroData.value;

        const linhas = tabela.querySelectorAll('.linha-tabela');
        let visiveis = 0;

        linhas.forEach(linha => {
            const lTexto = linha.dataset.texto.toLowerCase();
            const lStatus = linha.dataset.status.toLowerCase();
            const lVendedor = linha.dataset.vendedor;
            const lData = linha.dataset.data;

            const matchTexto = texto === '' || lTexto.includes(texto);
            const matchStatus = status === '' || lStatus === status;
            const matchVendedor = vendedor === '' || lVendedor === vendedor;
            const matchData = data === '' || lData === data;

            if (matchTexto && matchStatus && matchVendedor && matchData) {
                linha.style.display = '';
                visiveis++;
            } else {
                linha.style.display = 'none';
            }
        });

        const semResultados = document.getElementById('semResultados');
        if (visiveis === 0) semResultados.classList.remove('hidden');
        else semResultados.classList.add('hidden');
    }

    if(filtroTexto) [filtroTexto, filtroStatus, filtroVendedor, filtroData].forEach(el => {
        el.addEventListener('input', filtrarTabelaCompleta);
    });


    // ============================================================
    // 3. ABERTURA E PREENCHIMENTO DO MODAL
    // ============================================================
    
    const btnsGerenciar = document.querySelectorAll('.btn-abrir-modal');
    
    btnsGerenciar.forEach(btn => {
        btn.addEventListener('click', function() {
            // Dados básicos
            const id = this.dataset.id;
            const cliente = this.dataset.cliente;
            const contato = this.dataset.contato;
            const descricao = this.dataset.descricao;
            const restante = parseFloat(this.dataset.restante);
            const status = this.dataset.status;
            const modo = this.dataset.modo; // 'simples' ou 'multipla'
            
            // Parse de JSONs
            let historico = {};
            let itens = [];
            
            try { historico = JSON.parse(this.dataset.historico); } catch (e) {}
            try { itens = JSON.parse(this.dataset.itens || '[]'); } catch (e) {}

            // 1. Preenche dados gerais
            preencherModal(id, cliente, contato, descricao, restante, status, historico);
            
            // 2. Renderiza a tabela de itens individuais (NOVO)
            renderizarItens(modo, itens);

            // 3. Exibe o modal
            modal.classList.remove('hidden');
        });
    });

    function preencherModal(id, cliente, contato, descricao, restante, status, historico) {
        // Textos
        document.getElementById('modalTitulo').innerText = `Serviço #${id} - ${cliente}`;
        document.getElementById('modalDescricao').innerText = descricao;
        document.getElementById('modalRestanteDisplay').innerText = restante.toFixed(2);
        document.getElementById('modalContato').innerText = contato || '--';
        
        // WhatsApp Link
        if(contato) {
            const zapNumero = contato.replace(/\D/g, '');
            if (zapNumero.length >= 10) {
                btnWhatsapp.href = `https://wa.me/55${zapNumero}`;
                btnWhatsapp.classList.remove('hidden');
            } else {
                btnWhatsapp.classList.add('hidden');
            }
        } else {
            btnWhatsapp.classList.add('hidden');
        }

        // Actions dos Forms
        formPagamento.action = `/vendas/servicos/${id}/pagamento`;
        formCancelar.action = `/vendas/servicos/${id}/cancelar`;

        // Reset Visual
        areaCancelamento.classList.add('hidden');
        divStatusActions.classList.remove('hidden');

        // Timeline
        montarTimeline(historico);

        // Lógica de Pagamento
        if (restante <= 0.01) {
            areaPagamento.classList.add('hidden');
            msgPago.classList.remove('hidden');
        } else {
            if (status !== 'cancelado') {
                areaPagamento.classList.remove('hidden');
                msgPago.classList.add('hidden');
                document.querySelector("input[name='tipo_recebimento'][value='parcial']").checked = true;
                toggleValorInput();
                
                // Data Hoje
                const hojeLocal = new Date();
                hojeLocal.setMinutes(hojeLocal.getMinutes() - hojeLocal.getTimezoneOffset());
                document.querySelector("input[name='data_pagamento']").value = hojeLocal.toISOString().split('T')[0];
            } else {
                areaPagamento.classList.add('hidden');
                msgPago.classList.add('hidden');
            }
        }

        // Botões Status Global
        gerarBotoesStatus(id, status);

        // Botão Cancelar
        const isTotalmentePago = (restante <= 0.01);
        if (status === 'cancelado' || (status === 'entregue' && isTotalmentePago)) {
            btnShowCancelar.classList.add('hidden');
        } else {
            btnShowCancelar.classList.remove('hidden');
        }
    }


    // ============================================================
    // 4. RENDERIZAÇÃO DE ITENS INDIVIDUAIS (NOVO)
    // ============================================================
    
    function renderizarItens(modo, itens) {
        tabelaItensModal.innerHTML = ''; // Limpa tabela
        
        // Só mostra se for modo múltiplo e tiver itens
        if (modo === 'multipla' && itens.length > 0) {
            containerItens.classList.remove('hidden');
            
            itens.forEach(item => {
                const tr = document.createElement('tr');
                tr.className = "border-b border-gray-50 last:border-0 hover:bg-gray-50 transition-colors";

                // Lógica de Status do ITEM
                let badgeClass = 'bg-gray-100 text-gray-600';
                let labelStatus = 'Pendente';
                let htmlAcoes = '';
                
                // Define botões baseados no status atual do item
                if (item.status === 'pendente') {
                    badgeClass = 'bg-gray-200 text-gray-700';
                    labelStatus = 'Pendente';
                    htmlAcoes = `<a href="/vendas/itens/${item.id}/status/producao" class="inline-flex items-center px-2 py-1 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded transition-colors shadow-sm">
                                    <i data-lucide="hammer" class="w-3 h-3 mr-1"></i> Produzir
                                 </a>`;
                
                } else if (item.status === 'producao') {
                    badgeClass = 'bg-blue-100 text-blue-700 animate-pulse';
                    labelStatus = 'Em Produção';
                    htmlAcoes = `<a href="/vendas/itens/${item.id}/status/pronto" class="inline-flex items-center px-2 py-1 bg-yellow-500 hover:bg-yellow-600 text-white text-xs font-bold rounded transition-colors shadow-sm">
                                    <i data-lucide="package" class="w-3 h-3 mr-1"></i> Pronto
                                 </a>`;
                
                } else if (item.status === 'pronto') {
                    badgeClass = 'bg-yellow-100 text-yellow-700';
                    labelStatus = 'Pronto';
                    htmlAcoes = `<a href="/vendas/itens/${item.id}/status/entregue" class="inline-flex items-center px-2 py-1 bg-green-600 hover:bg-green-700 text-white text-xs font-bold rounded transition-colors shadow-sm">
                                    <i data-lucide="truck" class="w-3 h-3 mr-1"></i> Entregar
                                 </a>`;
                
                } else if (item.status === 'entregue') {
                    badgeClass = 'bg-green-100 text-green-700';
                    labelStatus = 'Entregue';
                    htmlAcoes = `<span class="text-green-600"><i data-lucide="check-circle-2" class="w-5 h-5"></i></span>`;
                }

                // Monta o HTML da linha
                tr.innerHTML = `
                    <td class="p-3">
                        <div class="font-bold text-navy-900 text-sm">${item.qtd}x ${item.descricao}</div>
                        <div class="text-xs text-gray-500">${item.cor}</div>
                    </td>
                    <td class="p-3 text-center">
                        <span class="px-2 py-1 rounded-full text-[10px] uppercase font-bold tracking-wide ${badgeClass}">${labelStatus}</span>
                    </td>
                    <td class="p-3 text-right">
                        ${htmlAcoes}
                    </td>
                `;
                tabelaItensModal.appendChild(tr);
            });
            
            // Importante: Recarrega ícones Lucide dentro da tabela dinâmica
            if(typeof lucide !== 'undefined') lucide.createIcons();
            
        } else {
            // Venda Simples: Esconde a tabela de itens
            containerItens.classList.add('hidden');
        }
    }


    // ============================================================
    // 5. TIMELINE E STATUS GERAL
    // ============================================================

    function montarTimeline(historico) {
        let html = '';
        html += criarItemTimeline('Solicitação Criada', historico.criado_em, historico.vendedor, true);
        if (historico.data_producao) html += criarItemTimeline('Iniciou Produção (Geral)', historico.data_producao, historico.user_producao, true);
        if (historico.data_pronto) html += criarItemTimeline('Pronto p/ Retirada (Geral)', historico.data_pronto, historico.user_pronto, true);
        if (historico.data_entrega) html += criarItemTimeline('Entregue ao Cliente', historico.data_entrega, historico.user_entrega, true);
        
        if (historico.data_cancelamento) {
            html += `
            <div class="timeline-item">
                <div class="timeline-dot" style="background-color: #ef4444; border-color: #ef4444;"></div>
                <p class="text-sm font-bold text-red-600">Serviço Cancelado</p>
                <div class="flex justify-between items-center text-xs text-gray-500 mt-0.5">
                    <span>${formatData(historico.data_cancelamento)}</span>
                    <span class="bg-red-50 px-1.5 py-0.5 rounded text-red-600 border border-red-100">${historico.user_cancelamento || 'Admin'}</span>
                </div>
                <p class="text-xs text-gray-500 mt-1 italic border-l-2 border-red-200 pl-2">Motivo: "${historico.motivo_cancelamento}"</p>
            </div>`;
        }
        timelineContainer.innerHTML = html;
    }

    function criarItemTimeline(titulo, dataStr, usuario, ativo) {
        if (!dataStr) return '';
        const classeDot = ativo ? 'active' : 'inactive';
        return `
            <div class="timeline-item">
                <div class="timeline-dot ${classeDot}"></div>
                <p class="text-sm font-bold text-navy-900">${titulo}</p>
                <div class="flex justify-between items-center text-xs text-gray-500 mt-0.5">
                    <span>${formatData(dataStr)}</span>
                    <span class="bg-gray-100 px-1.5 py-0.5 rounded text-gray-600 border border-gray-200">${usuario || 'Sistema'}</span>
                </div>
            </div>
        `;
    }

    function formatData(dataStr) {
        if(!dataStr) return '';
        const d = new Date(dataStr);
        return d.toLocaleDateString('pt-BR') + ' ' + d.toLocaleTimeString('pt-BR', {hour: '2-digit', minute:'2-digit'});
    }

    function gerarBotoesStatus(id, status) {
        let html = '';
        const btnClass = "px-4 py-2 text-white rounded shadow transition-colors text-sm font-bold flex-1 text-center block";

        if (status === 'pendente') {
            html = `<a href="/vendas/servicos/${id}/status/producao" class="${btnClass} bg-blue-600 hover:bg-blue-700">Iniciar Produção (Tudo)</a>`;
        } else if (status === 'producao') {
            html = `<a href="/vendas/servicos/${id}/status/pronto" class="${btnClass} bg-yellow-500 hover:bg-yellow-600">Marcar Pronto (Tudo)</a>`;
        } else if (status === 'pronto') {
            html = `<a href="/vendas/servicos/${id}/status/entregue" class="${btnClass} bg-green-600 hover:bg-green-700">Entregar (Tudo)</a>`;
        } else if (status === 'entregue') {
            html = `<span class="text-gray-400 text-sm italic w-full text-center flex items-center justify-center"><i data-lucide="check-circle" class="w-4 h-4 mr-1"></i> Finalizado</span>`;
        } else if (status === 'cancelado') {
            html = `<span class="text-red-500 text-sm font-bold w-full text-center uppercase border border-red-200 bg-red-50 py-2 rounded">Cancelado</span>`;
        }
        botoesStatus.innerHTML = html;
        if(typeof lucide !== 'undefined') lucide.createIcons();
    }


    // ============================================================
    // 6. UX (MOSTRAR/ESCONDER)
    // ============================================================

    if(btnShowCancelar) {
        btnShowCancelar.addEventListener('click', function() {
            divStatusActions.classList.add('hidden');
            areaPagamento.classList.add('hidden');
            areaCancelamento.classList.remove('hidden');
        });
    }

    if(btnAbortarCancelamento) {
        btnAbortarCancelamento.addEventListener('click', function() {
            areaCancelamento.classList.add('hidden');
            divStatusActions.classList.remove('hidden');
            const restante = parseFloat(document.getElementById('modalRestanteDisplay').innerText);
            if(restante > 0.01) areaPagamento.classList.remove('hidden');
        });
    }

    function toggleValorInput() {
        const radioChecked = document.querySelector('input[name="tipo_recebimento"]:checked');
        if(!radioChecked) return;
        const tipo = radioChecked.value;
        const divInput = document.getElementById('divValorInput');
        const inputVal = document.querySelector('input[name="valor"]');
        
        if (tipo === 'total') {
            divInput.classList.add('opacity-50', 'pointer-events-none');
            inputVal.required = false;
            inputVal.value = '';
        } else {
            divInput.classList.remove('opacity-50', 'pointer-events-none');
            inputVal.required = true;
        }
    }
    radiosTipo.forEach(radio => radio.addEventListener('change', toggleValorInput));


    // ============================================================
    // 7. FECHAR MODAL
    // ============================================================
    function fecharModalFunc() {
        modal.classList.add('hidden');
    }
    if(btnFechar) btnFechar.addEventListener('click', fecharModalFunc);
    if(overlay) overlay.addEventListener('click', fecharModalFunc);
});