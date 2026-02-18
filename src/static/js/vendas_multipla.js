document.addEventListener('DOMContentLoaded', function() {
    
    // Recupera produtos do atributo data-produtos do formulário
    let PRODUTOS_DISPONIVEIS = [];
    const form = document.getElementById('formMultiplo');
    if(form && form.dataset.produtos) {
        try {
            PRODUTOS_DISPONIVEIS = JSON.parse(form.dataset.produtos);
        } catch(e) { console.error("Erro JSON produtos:", e); }
    }

    let contadorLinhas = 0;
    const tbody = document.getElementById('listaItens');
    const emptyState = document.getElementById('emptyStateItens');

    // --- FUNÇÃO ADICIONAR LINHA ---
    window.adicionarLinha = function() {
        if(emptyState) emptyState.classList.add('hidden');
        
        const index = contadorLinhas++;
        
        let optionsProd = '<option value="">Selecione...</option>';
        PRODUTOS_DISPONIVEIS.forEach(p => {
            optionsProd += `<option value="${p.id}" data-m2="${p.preco_m2}" data-m3="${p.preco_m3}">${p.nome}</option>`;
        });

        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50 transition-colors group';
        row.id = `linha-${index}`;
        
        row.innerHTML = `
            <td class="p-2 align-top">
                <input type="text" name="itens[${index}][descricao]" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-navy-900 outline-none" placeholder="Ex: Pintura Portão" required>
            </td>
            <td class="p-2 align-top">
                <select name="itens[${index}][produto_id]" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-navy-900 outline-none" required>
                    ${optionsProd}
                </select>
            </td>
            <td class="p-2 align-top">
                <input type="number" name="itens[${index}][qtd]" id="qtd-${index}" value="1" min="0.1" step="0.1" 
                       class="w-full px-2 py-2 border border-gray-300 rounded-lg text-center text-sm font-bold focus:ring-2 focus:ring-navy-900 outline-none" 
                       oninput="calcLinha(${index}, 'qtd')" required>
            </td>
            <td class="p-2 align-top">
                <input type="number" name="itens[${index}][unit]" id="unit-${index}" min="0.01" step="0.01" 
                       class="w-full px-2 py-2 border border-gray-300 rounded-lg text-right text-sm focus:ring-2 focus:ring-navy-900 outline-none" 
                       placeholder="0.00" oninput="calcLinha(${index}, 'unit')" required>
            </td>
            <td class="p-2 align-top">
                <input type="number" name="itens[${index}][total]" id="total-${index}" min="0.01" step="0.01" 
                       class="w-full px-2 py-2 border border-gray-300 rounded-lg bg-gray-100 text-right text-sm font-bold text-navy-900 focus:ring-2 focus:ring-navy-900 outline-none" 
                       placeholder="0.00" oninput="calcLinha(${index}, 'total')" required>
            </td>
            <td class="p-2 text-center align-top pt-3">
                <button type="button" onclick="removerLinha(${index})" class="text-gray-400 hover:text-red-600 transition-colors p-1 rounded-full hover:bg-red-50">
                    <i data-lucide="trash-2" class="w-4 h-4"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
        
        if(typeof lucide !== 'undefined') lucide.createIcons();
    };

    // --- REMOVER LINHA ---
    window.removerLinha = function(index) {
        const linha = document.getElementById(`linha-${index}`);
        if(linha) linha.remove();
        if(tbody.children.length === 0) {
            if(emptyState) emptyState.classList.remove('hidden');
        }
        calcularFinal();
    };

    // --- CÁLCULO DE LINHA (BIDIRECIONAL) ---
    window.calcLinha = function(idx, origem) {
        const qtdEl = document.getElementById(`qtd-${idx}`);
        const unitEl = document.getElementById(`unit-${idx}`);
        const totalEl = document.getElementById(`total-${idx}`);

        let qtd = parseFloat(qtdEl.value) || 0;
        let unit = parseFloat(unitEl.value) || 0;
        let total = parseFloat(totalEl.value) || 0;
        
        if (origem === 'qtd') {
            if (unit > 0) totalEl.value = (qtd * unit).toFixed(2);
            else if (total > 0 && qtd > 0) unitEl.value = (total / qtd).toFixed(2);
        } 
        else if (origem === 'unit') {
            totalEl.value = (qtd * unit).toFixed(2);
        } 
        else if (origem === 'total') {
            if (qtd > 0) unitEl.value = (total / qtd).toFixed(2);
        }
        
        calcularFinal();
    };

    // --- CÁLCULO FINAL ---
    window.calcularTotal = function() {
        let subtotal = 0;
        const inputsTotal = document.querySelectorAll('input[name*="[total]"]');
        inputsTotal.forEach(inp => { subtotal += parseFloat(inp.value) || 0; });
        
        // Atualiza Subtotal
        const displaySub = document.getElementById('displaySubtotal');
        if(displaySub) displaySub.innerText = subtotal.toFixed(2);

        // Pega valores do componente Financeiro
        const acrescimo = parseFloat(document.getElementById('inputAcrescimo').value) || 0;
        
        // Verifica se é form Flask ou input manual para o desconto
        let descValor = 0;
        let descTipo = 'sem';
        
        const inputDescFlask = document.getElementById('valor_desconto_aplicado');
        const inputDescManual = document.getElementById('inputDesconto');
        
        if(inputDescFlask) descValor = parseFloat(inputDescFlask.value) || 0;
        else if(inputDescManual) descValor = parseFloat(inputDescManual.value) || 0;

        // Verifica radio de desconto
        const radiosTipo = document.getElementsByName('tipo_desconto');
        for(let r of radiosTipo) {
            if(r.checked) {
                descTipo = r.value;
                break;
            }
        }

        let baseCalculo = subtotal + acrescimo;
        let descontoReais = 0;

        if (descTipo === 'perc') {
            descontoReais = baseCalculo * (descValor / 100);
        } else if (descTipo === 'real') {
            descontoReais = descValor;
        }

        let final = baseCalculo - descontoReais;
        if (final < 0) final = 0;

        // Atualiza Displays do Componente Financeiro
        document.getElementById('displayBase').innerText = `R$ ${subtotal.toFixed(2)}`;
        document.getElementById('displayAcrescimo').innerText = `+ R$ ${acrescimo.toFixed(2)}`;
        document.getElementById('displayDesconto').innerText = `- R$ ${descontoReais.toFixed(2)}`;
        document.getElementById('displayTotal').innerText = `R$ ${final.toFixed(2)}`;
        
        // Atualiza inputs ocultos se existirem (para submit)
        const hiddenTotal = document.getElementById('hiddenTotalFinal'); // Se houver no HTML legado
        if(hiddenTotal) hiddenTotal.value = final.toFixed(2);
    };
    
    // Alias para compatibilidade
    window.calcularFinal = window.calcularTotal;

    // --- TOGGLE DESCONTO ---
    window.toggleDesconto = function() {
        const radios = document.getElementsByName('tipo_desconto');
        let tipo = 'sem';
        for(let r of radios) if(r.checked) tipo = r.value;
        
        const inputManual = document.getElementById('inputDesconto');
        
        if(inputManual) {
            if(tipo === 'sem') {
                inputManual.disabled = true;
                inputManual.value = '0.00';
            } else {
                inputManual.disabled = false;
            }
        }
        calcularTotal();
    };

    // --- LÓGICA DE CLIENTE (Toggle PF/PJ) ---
    window.alternarTipoCliente = function(tipo) {
        const areaPf = document.getElementById('campos-pf');
        const areaPj = document.getElementById('campos-pj');
        
        if (!areaPf || !areaPj) return; // Proteção

        if (tipo === 'PF') {
            areaPf.classList.remove('hidden');
            areaPj.classList.add('hidden');
            
            // Ajusta required
            areaPf.querySelectorAll('input').forEach(i => { if(i.name !== 'pf_cpf') i.required = true; });
            areaPj.querySelectorAll('input').forEach(i => i.required = false);
        } else {
            areaPf.classList.add('hidden');
            areaPj.classList.remove('hidden');
            
            areaPf.querySelectorAll('input').forEach(i => i.required = false);
            areaPj.querySelectorAll('input').forEach(i => { if(i.name !== 'pj_cnpj') i.required = true; });
        }
    };
    
    // Alias para compatibilidade com código antigo se necessário
    window.toggleTipoCliente = function() {
        const select = document.getElementById('tipo_cliente');
        // Se for select (legado) ou radio
        if(select && select.tagName === 'SELECT') alternarTipoCliente(select.value);
    }

    // --- MÁSCARAS ---
    window.mascaraCpf = function(i){
        let v = i.value.replace(/\D/g,"");
        v=v.replace(/(\d{3})(\d)/,"$1.$2");
        v=v.replace(/(\d{3})(\d)/,"$1.$2");
        v=v.replace(/(\d{3})(\d{1,2})$/,"$1-$2");
        i.value = v.substring(0, 14);
    }
    window.mascaraCnpj = function(i){
        let v = i.value.replace(/\D/g,"");
        v=v.replace(/^(\d{2})(\d)/,"$1.$2");
        v=v.replace(/^(\d{2})\.(\d{3})(\d)/,"$1.$2.$3");
        v=v.replace(/\.(\d{3})(\d)/,".$1/$2");
        v=v.replace(/(\d{4})(\d)/,"$1-$2");
        i.value = v.substring(0, 18);
    }

    // --- VALIDAÇÃO AO ENVIAR ---
    const formSubmit = document.getElementById('formMultiplo');
    if(formSubmit) {
        formSubmit.addEventListener('submit', function(e) {
            const inputsUnit = document.querySelectorAll('input[name*="[unit]"]');
            
            if (inputsUnit.length === 0) {
                e.preventDefault();
                alert("Adicione pelo menos um item à venda.");
                return;
            }
            
            // Recalcula final antes de enviar para garantir
            calcularTotal();
        });
    }

    if(typeof lucide !== 'undefined') lucide.createIcons();
    
    // Inicialização
    if(document.querySelector('input[name="tipo_cliente"]:checked')) {
        alternarTipoCliente(document.querySelector('input[name="tipo_cliente"]:checked').value);
    } else {
        alternarTipoCliente('PF');
    }
    
    adicionarLinha(); 
});