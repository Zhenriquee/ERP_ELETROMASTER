// src/static/js/vendas_multipla.js

document.addEventListener('DOMContentLoaded', function() {
    
    // --- FUNÇÕES DE MÁSCARA MONETÁRIA GLOBAIS ---
    window.aplicarMascaraMoeda = function(input) {
        if(!input) return;
        input.type = 'text'; // Altera o tipo para aceitar vírgula e pontos
        
        if (input.value) {
            let val = input.value.replace(/\./g, '').replace(',', '.');
            if (!isNaN(parseFloat(val))) {
                let v = parseFloat(val).toFixed(2);
                v = v.replace('.', ',');
                v = v.replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
                input.value = v;
            }
        }

        input.addEventListener('input', function(e) {
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
    }

    window.lerValorLocal = function(el) {
        if (!el || !el.value) return 0;
        let v = el.value.replace(/\./g, '').replace(',', '.');
        return parseFloat(v) || 0;
    }

    window.formatarNoElemento = function(el, valor) {
        if (!el) return;
        let v = parseFloat(valor).toFixed(2);
        v = v.replace('.', ',');
        v = v.replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
        el.value = v;
    }

    // Aplica nos campos financeiros fixos
    ['inputAcrescimo', 'inputDesconto', 'valor_desconto_aplicado'].forEach(id => {
        aplicarMascaraMoeda(document.getElementById(id));
    });

    let PRODUTOS_DISPONIVEIS = [];
    const form = document.getElementById('formMultiplo');
    if(form && form.dataset.produtos) {
        try { PRODUTOS_DISPONIVEIS = JSON.parse(form.dataset.produtos); } catch(e) {}
    }

    let contadorLinhas = 0;
    const tbody = document.getElementById('listaItens');
    const emptyState = document.getElementById('emptyStateItens');

    // --- FUNÇÃO ADICIONAR LINHA DINÂMICA ---
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
                <input type="text" name="itens[${index}][unit]" id="unit-${index}" 
                       class="w-full px-2 py-2 border border-gray-300 rounded-lg text-right text-sm focus:ring-2 focus:ring-navy-900 outline-none" 
                       placeholder="0,00" oninput="calcLinha(${index}, 'unit')" required>
            </td>
            <td class="p-2 align-top">
                <input type="text" name="itens[${index}][total]" id="total-${index}" 
                       class="w-full px-2 py-2 border border-gray-300 rounded-lg bg-gray-100 text-right text-sm font-bold text-navy-900 focus:ring-2 focus:ring-navy-900 outline-none" 
                       placeholder="0,00" oninput="calcLinha(${index}, 'total')" required>
            </td>
            <td class="p-2 text-center align-top pt-3">
                <button type="button" onclick="removerLinha(${index})" class="text-gray-400 hover:text-red-600 transition-colors p-1 rounded-full hover:bg-red-50">
                    <i data-lucide="trash-2" class="w-4 h-4"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);

        // Ativa a máscara nas linhas recém criadas!
        aplicarMascaraMoeda(document.getElementById(`unit-${index}`));
        aplicarMascaraMoeda(document.getElementById(`total-${index}`));
        
        if(typeof lucide !== 'undefined') lucide.createIcons();
    };

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

    window.removerLinha = function(index) {
        const linha = document.getElementById(`linha-${index}`);
        if(linha) linha.remove();
        if(tbody.children.length === 0 && emptyState) emptyState.classList.remove('hidden');
        calcularFinal();
    };

    // --- CÁLCULO DA LINHA (Lendo sem as máscaras visualmente) ---
    window.calcLinha = function(idx, origem) {
        const qtdEl = document.getElementById(`qtd-${idx}`);
        const unitEl = document.getElementById(`unit-${idx}`);
        const totalEl = document.getElementById(`total-${idx}`);

        let qtd = 0;
        if(qtdEl && qtdEl.value) {
            qtd = parseFloat(qtdEl.value.replace(',', '.')) || 0;
        }
        
        let unit = lerValorLocal(unitEl);
        let total = lerValorLocal(totalEl);
        
        if (origem === 'qtd') {
            if (unit > 0) formatarNoElemento(totalEl, qtd * unit);
            else if (total > 0 && qtd > 0) formatarNoElemento(unitEl, total / qtd);
        } 
        else if (origem === 'unit') {
            formatarNoElemento(totalEl, qtd * unit);
        } 
        else if (origem === 'total') {
            if (qtd > 0) formatarNoElemento(unitEl, total / qtd);
        }
        
        calcularFinal();
    };

    window.calcularTotal = function() {
        let subtotal = 0;
        const inputsTotal = document.querySelectorAll('input[name*="[total]"]');
        inputsTotal.forEach(inp => { subtotal += lerValorLocal(inp); });
        
        const displaySub = document.getElementById('displaySubtotal');
        if(displaySub) displaySub.innerText = subtotal.toLocaleString('pt-BR', {minimumFractionDigits: 2});

        const acrescimo = lerValorLocal(document.getElementById('inputAcrescimo'));
        
        let descValor = 0;
        let descTipo = 'sem';
        
        const inputDescFlask = document.getElementById('valor_desconto_aplicado');
        const inputDescManual = document.getElementById('inputDesconto');
        
        if(inputDescFlask) descValor = lerValorLocal(inputDescFlask);
        else if(inputDescManual) descValor = lerValorLocal(inputDescManual);

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

        document.getElementById('displayBase').innerText = `R$ ${subtotal.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
        document.getElementById('displayAcrescimo').innerText = `+ R$ ${acrescimo.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
        document.getElementById('displayDesconto').innerText = `- R$ ${descontoReais.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
        document.getElementById('displayTotal').innerText = `R$ ${final.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
        
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
                inputManual.value = '';
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

    // --- BLOQUEADOR DE SUBMIT E LIMPEZA DE MÁSCARA ---
    const formSubmit = document.getElementById('formMultiplo');
    if(formSubmit) {
        formSubmit.addEventListener('submit', function(e) {
            
            // 1. Limite de Tamanho das Fotos
            const inputsArquivo = document.querySelectorAll('input[type="file"]');
            let tamanhoTotal = 0;
            const LIMITE_MB = 64; 
            const LIMITE_BYTES = LIMITE_MB * 1024 * 1024;

            inputsArquivo.forEach(input => {
                if (input.files) {
                    for (let i = 0; i < input.files.length; i++) {
                        tamanhoTotal += input.files[i].size;
                    }
                }
            });

            if (tamanhoTotal > LIMITE_BYTES) {
                e.preventDefault();
                const tamanhoAtualMB = (tamanhoTotal / (1024 * 1024)).toFixed(2);
                alert(`O tamanho total das imagens (${tamanhoAtualMB} MB) excede o limite permitido de ${LIMITE_MB} MB.\n\nPor favor, reduza o tamanho das fotos ou envie menos arquivos.`);
                return;
            }

            // 2. Validação de Itens
            const inputsUnit = document.querySelectorAll('input[name*="[unit]"]');
            if (inputsUnit.length === 0) {
                e.preventDefault();
                alert("Adicione pelo menos um item à venda.");
                return;
            }
            
            // 3. LIMPEZA ESTRUTURAL DAS MÁSCARAS ANTES DE CHEGAR NO SERVIDOR!
            const inputsMonetarios = document.querySelectorAll('input[name*="[unit]"], input[name*="[total]"], #inputAcrescimo, #inputDesconto, #valor_desconto_aplicado');
            inputsMonetarios.forEach(el => {
                if (el && el.value) {
                    el.value = el.value.replace(/\./g, '').replace(',', '.');
                }
            });

            const inputsQtd = document.querySelectorAll('input[name*="[qtd]"]');
            inputsQtd.forEach(el => {
                if (el && el.value) el.value = el.value.replace(',', '.');
            });
        });
    }

    // Inicialização
    if(typeof lucide !== 'undefined') lucide.createIcons();
    if(document.querySelector('input[name="tipo_cliente"]:checked')) {
        alternarTipoCliente(document.querySelector('input[name="tipo_cliente"]:checked').value);
    } else {
        alternarTipoCliente('PF');
    }
    
    adicionarLinha(); 
});