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
        
        // AQUI ESTÁ A MUDANÇA: Inclusão da coluna de Fotos
        row.innerHTML = `
            <td class="p-2 align-top">
                <input type="text" name="itens[${index}][descricao]" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-navy-900 outline-none" placeholder="Ex: Grade Janela" required>
            </td>
            <td class="p-2 align-top">
                <select name="itens[${index}][produto_id]" class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:ring-2 focus:ring-navy-900 outline-none" required>
                    ${optionsProd}
                </select>
            </td>
            
            <td class="p-2 align-top text-center">
                <label class="inline-flex flex-col items-center justify-center p-2 border border-dashed border-gray-400 rounded-lg cursor-pointer hover:bg-blue-50 hover:border-blue-500 transition-all text-gray-500 hover:text-blue-600 w-full h-full">
                    <i data-lucide="camera" class="w-4 h-4 mb-1"></i>
                    <span class="text-[10px] font-bold leading-none" id="label-foto-${index}">Add Foto</span>
                    <input type="file" name="itens[${index}][fotos]" multiple accept="image/*" class="hidden" onchange="atualizarLabelFoto(this, ${index})">
                </label>
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

    // --- FUNÇÃO PARA ATUALIZAR CONTADOR DE FOTOS ---
    window.atualizarLabelFoto = function(input, index) {
        const label = document.getElementById(`label-foto-${index}`);
        if(input.files && input.files.length > 0) {
            const qtd = input.files.length;
            label.innerText = qtd + (qtd === 1 ? ' Foto' : ' Fotos');
            label.classList.add('text-green-600');
        } else {
            label.innerText = 'Add Foto';
            label.classList.remove('text-green-600');
        }
    }

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
        
        let descValor = 0;
        let descTipo = 'sem';
        
        const inputDescFlask = document.getElementById('valor_desconto_aplicado');
        const inputDescManual = document.getElementById('inputDesconto');
        
        if(inputDescFlask) descValor = parseFloat(inputDescFlask.value) || 0;
        else if(inputDescManual) descValor = parseFloat(inputDescManual.value) || 0;

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

        document.getElementById('displayBase').innerText = `R$ ${subtotal.toFixed(2)}`;
        document.getElementById('displayAcrescimo').innerText = `+ R$ ${acrescimo.toFixed(2)}`;
        document.getElementById('displayDesconto').innerText = `- R$ ${descontoReais.toFixed(2)}`;
        document.getElementById('displayTotal').innerText = `R$ ${final.toFixed(2)}`;
        
        const hiddenTotal = document.getElementById('hiddenTotalFinal'); 
        if(hiddenTotal) hiddenTotal.value = final.toFixed(2);
    };
    
    window.calcularFinal = window.calcularTotal;

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

    window.alternarTipoCliente = function(tipo) {
        const areaPf = document.getElementById('campos-pf');
        const areaPj = document.getElementById('campos-pj');
        
        if (!areaPf || !areaPj) return;

        if (tipo === 'PF') {
            areaPf.classList.remove('hidden');
            areaPj.classList.add('hidden');
            areaPf.querySelectorAll('input').forEach(i => { if(i.name !== 'pf_cpf') i.required = true; });
            areaPj.querySelectorAll('input').forEach(i => i.required = false);
        } else {
            areaPf.classList.add('hidden');
            areaPj.classList.remove('hidden');
            areaPf.querySelectorAll('input').forEach(i => i.required = false);
            areaPj.querySelectorAll('input').forEach(i => { if(i.name !== 'pj_cnpj') i.required = true; });
        }
    };
    
    window.toggleTipoCliente = function() {
        const select = document.getElementById('tipo_cliente');
        if(select && select.tagName === 'SELECT') alternarTipoCliente(select.value);
    }

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

    const formSubmit = document.getElementById('formMultiplo');
    if(formSubmit) {
        formSubmit.addEventListener('submit', function(e) {
            const inputsUnit = document.querySelectorAll('input[name*="[unit]"]');
            
            if (inputsUnit.length === 0) {
                e.preventDefault();
                alert("Adicione pelo menos um item à venda.");
                return;
            }
            calcularTotal();
        });
    }

    if(typeof lucide !== 'undefined') lucide.createIcons();
    
    if(document.querySelector('input[name="tipo_cliente"]:checked')) {
        alternarTipoCliente(document.querySelector('input[name="tipo_cliente"]:checked').value);
    } else {
        alternarTipoCliente('PF');
    }
    
    adicionarLinha(); 
});