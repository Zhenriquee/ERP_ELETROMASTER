document.addEventListener('DOMContentLoaded', function() {
    
    // ==========================================
    // 1. SELEÇÃO DE ELEMENTOS DO DOM
    // ==========================================
    
    // Elementos Principais do Modal
    const modal = document.getElementById('modalServico');
    const overlay = document.getElementById('modalOverlay');
    const btnFechar = document.getElementById('btnFecharModal');
    
    // Sub-seções do Modal
    const divStatusActions = document.getElementById('divStatusActions'); // Botões de status
    const areaPagamento = document.getElementById('areaPagamento');       // Form de pagamento
    const areaCancelamento = document.getElementById('areaCancelamento'); // Form de cancelamento
    const msgPago = document.getElementById('msgPago');                   // Mensagem de pago
    const botoesStatus = document.getElementById('botoesStatus');         // Container dos botões
    const timelineContainer = document.getElementById('timelineContainer'); // Container da timeline
    
    // Formulários
    const formPagamento = document.getElementById('formPagamento');
    const formCancelar = document.getElementById('formCancelar');

    // Botões de Ação Específica
    const btnShowCancelar = document.getElementById('btnShowCancelar');         // Link "Cancelar Serviço"
    const btnAbortarCancelamento = document.getElementById('btnAbortarCancelamento'); // Botão "Voltar" do cancelamento
    const btnWhatsapp = document.getElementById('btnWhatsapp');                 // Botão Zap

    // Filtros da Tabela
    const filtroTexto = document.getElementById('filtroTexto');
    const filtroStatus = document.getElementById('filtroStatus');
    const filtroVendedor = document.getElementById('filtroVendedor');
    const filtroData = document.getElementById('filtroData');
    const tabela = document.getElementById('tabelaServicos');

    // Radios de Pagamento
    const radiosTipo = document.querySelectorAll('input[name="tipo_recebimento"]');


    // ============================================================
    // 2. FILTROS AVANÇADOS (LIVE SEARCH)
    // ============================================================
    function filtrarTabelaCompleta() {
        const texto = filtroTexto.value.toLowerCase();
        const status = filtroStatus.value.toLowerCase();
        const vendedor = filtroVendedor.value; // Exact match
        const data = filtroData.value; // YYYY-MM-DD

        const linhas = tabela.querySelectorAll('.linha-tabela');
        let visiveis = 0;

        linhas.forEach(linha => {
            // Lê os dados armazenados nos atributos data-*
            const lTexto = linha.dataset.texto.toLowerCase();
            const lStatus = linha.dataset.status.toLowerCase();
            const lVendedor = linha.dataset.vendedor;
            const lData = linha.dataset.data;

            // Lógica E (AND): A linha deve atender a TODOS os critérios preenchidos
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

        // Feedback Visual (Nenhum resultado)
        const semResultados = document.getElementById('semResultados');
        if (visiveis === 0) semResultados.classList.remove('hidden');
        else semResultados.classList.add('hidden');
    }

    // Adiciona Listeners aos inputs de filtro
    if(filtroTexto) [filtroTexto, filtroStatus, filtroVendedor, filtroData].forEach(el => {
        el.addEventListener('input', filtrarTabelaCompleta);
    });


    // ============================================================
    // 3. ABERTURA E PREENCHIMENTO DO MODAL
    // ============================================================
    
    // Captura cliques nos botões "Gerenciar" da tabela
    const btnsGerenciar = document.querySelectorAll('.btn-abrir-modal');
    
    btnsGerenciar.forEach(btn => {
        btn.addEventListener('click', function() {
            // Extrai dados do botão clicado
            const id = this.dataset.id;
            const cliente = this.dataset.cliente;
            const contato = this.dataset.contato;
            const descricao = this.dataset.descricao;
            const restante = parseFloat(this.dataset.restante);
            const status = this.dataset.status;
            
            // O histórico vem como string JSON segura, precisamos converter de volta para Objeto
            let historico = {};
            try {
                historico = JSON.parse(this.dataset.historico);
            } catch (e) {
                console.error("Erro ao ler histórico JSON", e);
            }

            preencherModal(id, cliente, contato, descricao, restante, status, historico);
            modal.classList.remove('hidden');
        });
    });

    function preencherModal(id, cliente, contato, descricao, restante, status, historico) {
        // 1. Textos Básicos
        document.getElementById('modalTitulo').innerText = `Serviço #${id} - ${cliente}`;
        document.getElementById('modalDescricao').innerText = descricao;
        document.getElementById('modalRestanteDisplay').innerText = restante.toFixed(2);
        
        // 2. Configura Links de Contato
        document.getElementById('modalContato').innerText = contato;
        if(contato) {
            const zapNumero = contato.replace(/\D/g, ''); // Remove tudo que não é número
            // Verifica se parece um celular válido (DDD + 9 dígitos = 11)
            if (zapNumero.length >= 10) {
                btnWhatsapp.href = `https://wa.me/55${zapNumero}`;
                btnWhatsapp.classList.remove('hidden');
            } else {
                btnWhatsapp.classList.add('hidden');
            }
        } else {
            btnWhatsapp.classList.add('hidden');
        }

        // 3. Configura Actions dos Forms (Para onde os dados serão enviados)
        formPagamento.action = `/vendas/servicos/${id}/pagamento`;
        formCancelar.action = `/vendas/servicos/${id}/cancelar`;

        // 4. Reseta Estado Visual (Esconde Cancelamento, Mostra Ações Normais)
        areaCancelamento.classList.add('hidden');
        divStatusActions.classList.remove('hidden');

        // 5. Constrói a Timeline
        montarTimeline(historico);

        // 6. Lógica de Pagamento
        // Se a dívida é 0 (ou quase), mostra mensagem de Pago. Senão, mostra form.
        if (restante <= 0.01) {
            areaPagamento.classList.add('hidden');
            msgPago.classList.remove('hidden');
        } else {
            // Se o serviço estiver cancelado, não deve permitir pagar
            if (status !== 'cancelado') {
                areaPagamento.classList.remove('hidden');
                msgPago.classList.add('hidden');
                
                // Reseta inputs do form de pagamento
                document.querySelector("input[name='tipo_recebimento'][value='parcial']").checked = true;
                toggleValorInput();
                
                // Define data padrão como Hoje (ajustando fuso horário local para o input date)
                const hojeLocal = new Date();
                hojeLocal.setMinutes(hojeLocal.getMinutes() - hojeLocal.getTimezoneOffset());
                document.querySelector("input[name='data_pagamento']").value = hojeLocal.toISOString().split('T')[0];
            } else {
                areaPagamento.classList.add('hidden');
                msgPago.classList.add('hidden');
            }
        }

        // 7. Botões de Mudança de Status
        gerarBotoesStatus(id, status);

        // 8. Lógica do Botão "Cancelar Serviço"
        // Bloqueia se já estiver cancelado OU (Entregue E Pago)
        const isTotalmentePago = (restante <= 0.01);
        if (status === 'cancelado' || (status === 'entregue' && isTotalmentePago)) {
            btnShowCancelar.classList.add('hidden');
        } else {
            btnShowCancelar.classList.remove('hidden');
        }
    }


    // ============================================================
    // 4. GERAÇÃO DINÂMICA DE CONTEÚDO
    // ============================================================

    function montarTimeline(historico) {
        let html = '';
        
        // Eventos Normais
        html += criarItemTimeline('Solicitação Criada', historico.criado_em, historico.vendedor, true);
        if (historico.data_producao) html += criarItemTimeline('Iniciou Produção', historico.data_producao, historico.user_producao, true);
        if (historico.data_pronto) html += criarItemTimeline('Pronto p/ Retirada', historico.data_pronto, historico.user_pronto, true);
        if (historico.data_entrega) html += criarItemTimeline('Entregue ao Cliente', historico.data_entrega, historico.user_entrega, true);
        
        // Evento Especial: Cancelamento
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
            html = `<a href="/vendas/servicos/${id}/status/producao" class="${btnClass} bg-blue-600 hover:bg-blue-700">Iniciar Produção</a>`;
        } else if (status === 'producao') {
            html = `<a href="/vendas/servicos/${id}/status/pronto" class="${btnClass} bg-yellow-500 hover:bg-yellow-600">Marcar Pronto</a>`;
        } else if (status === 'pronto') {
            html = `<a href="/vendas/servicos/${id}/status/entregue" class="${btnClass} bg-green-600 hover:bg-green-700">Confirmar Entrega</a>`;
        } else if (status === 'entregue') {
            html = `<span class="text-gray-400 text-sm italic w-full text-center flex items-center justify-center"><i data-lucide="check-circle" class="w-4 h-4 mr-1"></i> Finalizado</span>`;
        } else if (status === 'cancelado') {
            html = `<span class="text-red-500 text-sm font-bold w-full text-center uppercase border border-red-200 bg-red-50 py-2 rounded">Cancelado</span>`;
        }
        
        botoesStatus.innerHTML = html;
        if(typeof lucide !== 'undefined') lucide.createIcons(); // Recarrega ícones inseridos dinamicamente
    }


    // ============================================================
    // 5. INTERAÇÕES DE UX (MOSTRAR/ESCONDER SEÇÕES)
    // ============================================================

    // Botão "Cancelar Serviço" -> Mostra form de cancelamento
    if(btnShowCancelar) {
        btnShowCancelar.addEventListener('click', function() {
            divStatusActions.classList.add('hidden'); // Esconde botões normais
            areaPagamento.classList.add('hidden');    // Esconde pagamento
            areaCancelamento.classList.remove('hidden'); // Mostra área de perigo
        });
    }

    // Botão "Voltar" (dentro do cancelamento) -> Restaura estado
    if(btnAbortarCancelamento) {
        btnAbortarCancelamento.addEventListener('click', function() {
            areaCancelamento.classList.add('hidden');
            divStatusActions.classList.remove('hidden');
            
            // Se ainda deve, mostra pagamento de novo
            const restante = parseFloat(document.getElementById('modalRestanteDisplay').innerText);
            if(restante > 0.01) areaPagamento.classList.remove('hidden');
        });
    }

    // Controle do Input de Valor (Total vs Parcial)
    function toggleValorInput() {
        // Encontra qual radio está marcado
        const radioChecked = document.querySelector('input[name="tipo_recebimento"]:checked');
        if(!radioChecked) return;

        const tipo = radioChecked.value;
        const divInput = document.getElementById('divValorInput');
        const inputVal = document.querySelector('input[name="valor"]');
        
        if (tipo === 'total') {
            divInput.classList.add('opacity-50', 'pointer-events-none');
            inputVal.required = false;
            inputVal.value = ''; // Limpa para evitar confusão
        } else {
            divInput.classList.remove('opacity-50', 'pointer-events-none');
            inputVal.required = true;
        }
    }

    // Adiciona listener a todos os radios
    radiosTipo.forEach(radio => radio.addEventListener('change', toggleValorInput));


    // ============================================================
    // 6. CONTROLE DE FECHAMENTO DO MODAL
    // ============================================================
    function fecharModalFunc() {
        modal.classList.add('hidden');
    }

    if(btnFechar) btnFechar.addEventListener('click', fecharModalFunc);
    if(overlay) overlay.addEventListener('click', fecharModalFunc);

});