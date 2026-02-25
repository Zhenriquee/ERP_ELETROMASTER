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

    // --- ELEMENTOS DE RECORRÊNCIA E TIPO ---
    const toggleTipo = document.getElementById('toggleTipo');
    const areaEstoque = document.getElementById('area-estoque');
    const divDescricao = document.getElementById('div-descricao');
    const divCategoria = document.getElementById('div-categoria');
    const divTipoCusto = document.getElementById('div-tipo-custo');
    const areaExtras = document.getElementById('area-extras');
    
    const chkRecorrente = document.getElementById('checkRecorrente');
    const divRepeticoes = document.getElementById('div-repeticoes');
    const labelRecorrente = document.getElementById('labelRecorrente');
    const labelQtd = document.getElementById('labelQtd');
    const labelSulfixoQtd = document.getElementById('labelSulfixoQtd');
    const avisoParcelamento = document.getElementById('aviso-parcelamento');

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

    // --- 3. LÓGICA DE RECORRÊNCIA E PARCELAMENTO ---
    if (chkRecorrente && divRepeticoes) {
        chkRecorrente.addEventListener('change', function() {
            if (this.checked) {
                divRepeticoes.classList.remove('hidden');
            } else {
                divRepeticoes.classList.add('hidden');
            }
        });
        
        if (chkRecorrente.checked) divRepeticoes.classList.remove('hidden');
    }

    // --- 4. LÓGICA DO TIPO DE DESPESA (COMPRA x DESPESA) ---
    if (toggleTipo) {
        function atualizarInterfaceTipo() {
            if (toggleTipo.checked) {
                // MODO COMPRA DE ESTOQUE
                areaEstoque.classList.remove('hidden');
                divDescricao.classList.add('hidden');
                divCategoria.classList.add('hidden');
                divTipoCusto.classList.add('hidden');
                
                // Muda Recorrência para Parcelamento
                labelRecorrente.innerText = "Esta compra foi parcelada?";
                labelQtd.innerText = "Nº Parcelas:";
                labelSulfixoQtd.innerText = "x";
                if(avisoParcelamento) avisoParcelamento.classList.remove('hidden');
                
                // Força visualização do Fornecedor e Recorrência (agora parcelamento)
                if(divFornecedor) divFornecedor.classList.remove('hidden');
                
            } else {
                // MODO DESPESA COMUM
                areaEstoque.classList.add('hidden');
                divDescricao.classList.remove('hidden');
                divCategoria.classList.remove('hidden');
                divTipoCusto.classList.remove('hidden');
                
                // Restaura Recorrência padrão
                labelRecorrente.innerText = "Esta é uma despesa recorrente?";
                labelQtd.innerText = "Repetir por:";
                labelSulfixoQtd.innerText = "meses";
                if(avisoParcelamento) avisoParcelamento.classList.add('hidden');
                
                // Atualiza categoria para decidir sobre fornecedor
                if (selectCategoria) selectCategoria.dispatchEvent(new Event('change'));
            }
        }

        toggleTipo.addEventListener('change', atualizarInterfaceTipo);
        atualizarInterfaceTipo(); // Init
        
        // --- 7. MÁSCARA DE MOEDA (NOVA DESPESA) ---
    const inputValorDespesa = document.getElementById('valor');
    if (inputValorDespesa) {
        inputValorDespesa.type = 'text';

        // Formata valor inicial se a tela estiver no modo Edição
        if (inputValorDespesa.value) {
            let val = inputValorDespesa.value.replace(/\./g, '').replace(',', '.');
            if (!isNaN(parseFloat(val))) {
                let v = parseFloat(val).toFixed(2);
                v = v.replace('.', ',');
                v = v.replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
                inputValorDespesa.value = v;
            }
        }

        // Intercepta a digitação
        inputValorDespesa.addEventListener('input', function(e) {
            let v = e.target.value.replace(/\D/g, '');
            if (v === '') {
                e.target.value = '';
                return;
            }
            v = (parseFloat(v) / 100).toFixed(2);
            v = v.replace('.', ',');
            v = v.replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
            e.target.value = v;
        });

        // Limpa a máscara antes de enviar o form para o Python (WTForms) não recusar
        const formDespesa = inputValorDespesa.closest('form');
        if (formDespesa) {
            formDespesa.addEventListener('submit', function() {
                if (inputValorDespesa.value) {
                    inputValorDespesa.value = inputValorDespesa.value.replace(/\./g, '').replace(',', '.');
                }
            });
        }
    }
        // Adiciona a primeira linha de produto se a tabela estiver vazia E o modo for estoque
        const tbody = document.getElementById('listaProdutos');
        if (toggleTipo.checked && tbody && tbody.children.length === 0) {
            adicionarLinhaProduto();
        }
    }

    // --- 5. MÁSCARA CNPJ ---
    if (inputCNPJ) {
        inputCNPJ.addEventListener('input', function(e) {
            let x = e.target.value.replace(/\D/g, '').match(/(\d{0,2})(\d{0,3})(\d{0,3})(\d{0,4})(\d{0,2})/);
            e.target.value = !x[2] ? x[1] : x[1] + '.' + x[2] + (x[3] ? '.' : '') + x[3] + (x[4] ? '/' : '') + x[4] + (x[5] ? '-' : '') + x[5];
        });
    }

    // --- 6. FILTROS DO PAINEL ---
    const filtroPeriodo = document.getElementById('filtroPeriodo');
    const filtroTexto = document.getElementById('filtroTexto');
    
    if (filtroPeriodo) {
        window.aplicarFiltros = function() {
            const valorPeriodo = filtroPeriodo.value; 
            if(!valorPeriodo) return;
            const [mes, ano] = valorPeriodo.split('-');
            
            const params = new URLSearchParams(window.location.search);
            params.set('mes', mes);
            params.set('ano', ano);
            
            // LER NOVO FILTRO DE TEXTO E OUTROS
            ['filtroTexto', 'filtroCat', 'filtroStatus', 'filtroFornecedor', 'filtroPagamento', 'filtroTipo', 'filtroVencimento'].forEach(id => {
                const el = document.getElementById(id);
                const paramName = id.replace('filtro', '').toLowerCase(); 
                
                if(el && el.value) {
                    let key = paramName;
                    // Mapeamento manual para backend
                    if(key === 'cat') key = 'categoria';
                    if(key === 'tipo') key = 'tipo_custo';
                    if(key === 'pagamento') key = 'forma_pagamento';
                    if(key === 'texto') key = 'q'; // Mapeia 'filtroTexto' para 'q'
                    
                    params.set(key, el.value);
                } else if(el && !el.value) {
                    // Limpa do URL se o usuário apagou o conteúdo
                    let key = paramName;
                    if(key === 'texto') key = 'q';
                    params.delete(key);
                }
            });

            window.location.href = `/financeiro/?${params.toString()}`;
        }
        
        filtroPeriodo.addEventListener('change', window.aplicarFiltros);
        
        // Ativa a busca ao pressionar 'Enter' no campo de texto
        if (filtroTexto) {
            filtroTexto.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault(); // Evita recarregar página fora do controle
                    window.aplicarFiltros();
                }
            });
        }
    }
});

// =========================================================
// FUNÇÕES GLOBAIS (FORA DO DOMContentLoaded)
// Isso garante que o botão HTML onclick="adicionarLinhaProduto()" encontre a função
// =========================================================

// =========================================================
// FUNÇÕES GLOBAIS (FORA DO DOMContentLoaded)
// =========================================================

function adicionarLinhaProduto() {
    const tbody = document.getElementById('listaProdutos');
    const emptyState = document.getElementById('emptyProdutos');
    const templateSelect = document.getElementById('templateProdutoSelect');
    
    if (!tbody || !templateSelect) {
        console.error("Elementos da tabela não encontrados.");
        return;
    }
    
    if (emptyState) emptyState.classList.add('hidden');

    const tr = document.createElement('tr');
    tr.className = "hover:bg-gray-50 border-b border-gray-100";
    
    const optionsHtml = templateSelect.innerHTML;
    
    tr.innerHTML = `
        <td class="p-2 align-top">
            <select name="produtos_ids[]" onchange="atualizarUnidadeDespesa(this)" class="w-full p-2 border border-gray-300 rounded bg-white focus:ring-2 focus:ring-navy-900 outline-none text-sm" required>
                ${optionsHtml}
            </select>
        </td>
        <td class="p-2 align-top">
            <div class="relative">
                <input type="number" name="quantidades[]" step="0.001" min="0.001" placeholder="Ex: 25.000" class="w-full p-2 pr-10 border border-gray-300 rounded outline-none text-sm" required>
                <span class="unidade-display absolute right-3 top-2 text-xs font-bold text-gray-400">UN</span>
            </div>
            <p class="text-[10px] text-gray-500 mt-1">Informe a Qtd em <span class="unidade-texto font-bold">UN</span>.</p>
        </td>
        <td class="p-2 text-center align-top pt-2">
            <button type="button" onclick="removerLinhaProduto(this)" class="text-red-400 hover:text-red-600 transition-colors p-1 rounded hover:bg-red-50">
                <i data-lucide="trash-2" class="w-4 h-4"></i>
            </button>
        </td>
    `;
    
    tbody.appendChild(tr);
    
    if(typeof lucide !== 'undefined') lucide.createIcons();
}

// NOVA FUNÇÃO: Atualiza a unidade escrita ao lado do campo (ex: muda de UN para KG automaticamente)
function atualizarUnidadeDespesa(selectElement) {
    const tr = selectElement.closest('tr');
    const unidadeDisplay = tr.querySelector('.unidade-display');
    const unidadeTexto = tr.querySelector('.unidade-texto');
    
    const option = selectElement.options[selectElement.selectedIndex];
    let unidade = 'UN';
    
    // Pega a unidade direto da opção selecionada (que vem do banco de dados)
    if (option && option.getAttribute('data-unidade')) {
        unidade = option.getAttribute('data-unidade');
    }
    
    if (unidadeDisplay) unidadeDisplay.innerText = unidade;
    if (unidadeTexto) unidadeTexto.innerText = unidade;
}

function removerLinhaProduto(btn) {
    const tr = btn.closest('tr');
    tr.remove();
    
    const tbody = document.getElementById('listaProdutos');
    const emptyState = document.getElementById('emptyProdutos');
    
    if (tbody && tbody.children.length === 0 && emptyState) {
        emptyState.classList.remove('hidden');
    }
}