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

    const btnsAbrir = document.querySelectorAll('.btn-abrir-modal');
    btnsAbrir.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const d = this.dataset;
            
            document.getElementById('modalTitulo').innerText = `Serviço #${d.id} - ${d.cliente}`;
            document.getElementById('modalDescricao').innerText = d.descricao;
            document.getElementById('modalContato').innerText = d.contato || '--';
            
            if(d.contato) {
                const num = d.contato.replace(/\D/g, '');
                if(num.length >= 10) {
                    btnWhatsapp.href = `https://wa.me/55${num}`;
                    btnWhatsapp.classList.remove('hidden');
                } else { btnWhatsapp.classList.add('hidden'); }
            } else { btnWhatsapp.classList.add('hidden'); }

            try {
                const hist = JSON.parse(d.historico);
                document.getElementById('modalVendedor').innerText = hist.vendedor || '--';
                document.getElementById('modalDataVenda').innerText = formatarData(hist.criado_em);
                montarTimeline(hist);
            } catch(e) { console.error('Erro historico', e); }

            gerarBotoesStatus(d.id, d.status);

            if(document.getElementById('modalRestanteDisplay')) {
                const restante = parseFloat(d.restante);
                
                // Formatação manual para o modal, já que é dinâmico
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
            
            if(tabs.length > 0) tabs[0].click();
            modal.classList.remove('hidden');
        });
    });

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