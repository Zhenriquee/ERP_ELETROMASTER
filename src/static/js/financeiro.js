// src/static/js/financeiro.js

document.addEventListener('DOMContentLoaded', function() {
    
    // --- ELEMENTOS ---
    const selectFormaPagamento = document.getElementById('forma_pagamento');
    const selectCategoria = document.getElementById('categoria');
    
    // Elementos da Nova Despesa
    const divCodigoBarras = document.getElementById('div-codigo-barras');
    const divFornecedor = document.getElementById('div-fornecedor');
    const divFuncionario = document.getElementById('div-funcionario');
    const inputCNPJ = document.getElementById('cnpj');

    // --- ELEMENTOS DE RECORRÊNCIA (NOVO) ---
    const chkRecorrente = document.getElementById('recorrente');
    const divRepeticoes = document.getElementById('div-repeticoes');

    // --- 1. LÓGICA DE PAGAMENTO (Boleto/Pix) ---
    if (selectFormaPagamento) {
        function atualizarCamposPagamento() {
            const valor = selectFormaPagamento.value;
            if (valor === 'boleto' || valor === 'pix') {
                if(divCodigoBarras) divCodigoBarras.classList.remove('hidden');
            } else {
                if(divCodigoBarras) divCodigoBarras.classList.add('hidden');
            }
        }
        selectFormaPagamento.addEventListener('change', atualizarCamposPagamento);
        atualizarCamposPagamento(); 
    }

    // --- 2. LÓGICA DE CATEGORIA ---
    if (selectCategoria) {
        function atualizarCamposCategoria() {
            const cat = selectCategoria.value;
            
            if(divFornecedor) divFornecedor.classList.add('hidden');
            if(divFuncionario) divFuncionario.classList.add('hidden');

            if (cat === 'pessoal') {
                if(divFuncionario) divFuncionario.classList.remove('hidden');
            } 
            else if (['material', 'infraestrutura', 'manutencao', 'marketing'].includes(cat)) {
                if(divFornecedor) divFornecedor.classList.remove('hidden');
            }
        }
        selectCategoria.addEventListener('change', atualizarCamposCategoria);
        atualizarCamposCategoria();
    }

    // --- 3. LÓGICA DE RECORRÊNCIA (AQUI ESTÁ O CÓDIGO NOVO) ---
    if (chkRecorrente && divRepeticoes) {
        chkRecorrente.addEventListener('change', function() {
            if (this.checked) {
                divRepeticoes.classList.remove('hidden');
            } else {
                divRepeticoes.classList.add('hidden');
            }
        });
        
        // Garante estado correto se a página recarregar com erro de validação
        if (chkRecorrente.checked) {
            divRepeticoes.classList.remove('hidden');
        } else {
            divRepeticoes.classList.add('hidden');
        }
    }

    // --- 4. MÁSCARA CNPJ ---
    if (inputCNPJ) {
        inputCNPJ.addEventListener('input', function(e) {
            let x = e.target.value.replace(/\D/g, '').match(/(\d{0,2})(\d{0,3})(\d{0,3})(\d{0,4})(\d{0,2})/);
            e.target.value = !x[2] ? x[1] : x[1] + '.' + x[2] + (x[3] ? '.' : '') + x[3] + (x[4] ? '/' : '') + x[4] + (x[5] ? '-' : '') + x[5];
        });
    }

// --- 5. FILTROS DO PAINEL (ATUALIZADO) ---
    const filtroPeriodo = document.getElementById('filtroPeriodo');
    const filtroCat = document.getElementById('filtroCat');
    const filtroStatus = document.getElementById('filtroStatus');
    const filtroFornecedor = document.getElementById('filtroFornecedor');
    const filtroPagamento = document.getElementById('filtroPagamento');
    const filtroTipo = document.getElementById('filtroTipo');
    const filtroVencimento = document.getElementById('filtroVencimento');

    if (filtroPeriodo) {
        // Agora esta função está global para ser chamada pelo botão "Aplicar Filtros"
        window.aplicarFiltros = function() {
            // Período (Obrigatório)
            const valorPeriodo = filtroPeriodo.value; 
            const [mes, ano] = valorPeriodo.split('-');

            const params = new URLSearchParams();
            params.append('mes', mes);
            params.append('ano', ano);
            
            // Filtros Opcionais (só adiciona se tiver valor)
            if (filtroCat && filtroCat.value) params.append('categoria', filtroCat.value);
            if (filtroStatus && filtroStatus.value) params.append('status', filtroStatus.value);
            if (filtroFornecedor && filtroFornecedor.value) params.append('fornecedor', filtroFornecedor.value);
            if (filtroPagamento && filtroPagamento.value) params.append('forma_pagamento', filtroPagamento.value);
            if (filtroTipo && filtroTipo.value) params.append('tipo_custo', filtroTipo.value);
            if (filtroVencimento && filtroVencimento.value) params.append('vencimento', filtroVencimento.value);

            window.location.href = `/financeiro/?${params.toString()}`;
        }

        // Evento apenas no Período (para troca rápida)
        filtroPeriodo.addEventListener('change', window.aplicarFiltros);
    }
});