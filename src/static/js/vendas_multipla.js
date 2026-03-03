// src/static/js/vendas_multipla.js

// --- VARIÁVEIS GLOBAIS ---
let PRODUTOS_DISPONIVEIS = [];
let contadorLinhas = 0;

// --- FUNÇÕES DE MÁSCARA E MATEMÁTICA ---
window.aplicarMascaraMoeda = function(input, callback) {
    if(!input) return;
    
    input.removeAttribute('oninput'); 
    input.type = 'text';
    
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
        } else {
            v = (parseFloat(v) / 100).toFixed(2);
            v = v.replace('.', ',');
            v = v.replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
            e.target.value = v;
        }
        
        // Garante que o cálculo aconteça DEPOIS da máscara
        if(typeof callback === 'function') {
            callback();
        }
    });
};

window.lerValorLocal = function(el) {
    if (!el || !el.value) return 0;
    let v = el.value.replace(/\./g, '').replace(',', '.');
    return parseFloat(v) || 0;
};

window.formatarNoElemento = function(el, valor) {
    if (!el) return;
    let v = parseFloat(valor).toFixed(2);
    v = v.replace('.', ',');
    v = v.replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
    el.value = v;
};

// --- FUNÇÕES DE INTERFACE DA TABELA ---
window.adicionarLinha = function() {
    const tbody = document.getElementById('listaItens');
    const emptyState = document.getElementById('emptyStateItens');
    
    if (!tbody) return; 
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
                <input type="file" name="itens[${index}][fotos]" multiple accept="image/*" class="hidden" onchange="window.atualizarLabelFoto(this, ${index})">
            </label>
        </td>
        <td class="p-2 align-top">
            <input type="number" name="itens[${index}][qtd]" id="qtd-${index}" value="1" min="0.1" step="0.1" 
                   class="w-full px-2 py-2 border border-gray-300 rounded-lg text-center text-sm font-bold focus:ring-2 focus:ring-navy-900 outline-none" 
                   oninput="window.calcLinha(${index}, 'qtd')" required>
        </td>
        <td class="p-2 align-top">
            <input type="text" name="itens[${index}][unit]" id="unit-${index}" 
                   class="w-full px-2 py-2 border border-gray-300 rounded-lg text-right text-sm focus:ring-2 focus:ring-navy-900 outline-none" 
                   placeholder="0,00" required>
        </td>
        <td class="p-2 align-top">
            <input type="text" name="itens[${index}][total]" id="total-${index}" 
                   class="w-full px-2 py-2 border border-gray-300 rounded-lg bg-gray-100 text-right text-sm font-bold text-navy-900 focus:ring-2 focus:ring-navy-900 outline-none" 
                   placeholder="0,00" required>
        </td>
        <td class="p-2 text-center align-top pt-3">
            <button type="button" onclick="window.removerLinha(${index})" class="text-gray-400 hover:text-red-600 transition-colors p-1 rounded-full hover:bg-red-50">
                <i data-lucide="trash-2" class="w-4 h-4"></i>
            </button>
        </td>
    `;
    tbody.appendChild(row);

    // O segredo: A máscara chama o cálculo via função anônima, garantindo a ordem
    window.aplicarMascaraMoeda(document.getElementById(`unit-${index}`), function() { window.calcLinha(index, 'unit'); });
    window.aplicarMascaraMoeda(document.getElementById(`total-${index}`), function() { window.calcLinha(index, 'total'); });
    
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
};

window.removerLinha = function(index) {
    const linha = document.getElementById(`linha-${index}`);
    if(linha) linha.remove();
    
    const tbody = document.getElementById('listaItens');
    const emptyState = document.getElementById('emptyStateItens');
    if(tbody && tbody.children.length === 0 && emptyState) emptyState.classList.remove('hidden');
    window.calcularTotal();
};

window.calcLinha = function(idx, origem) {
    const qtdEl = document.getElementById(`qtd-${idx}`);
    const unitEl = document.getElementById(`unit-${idx}`);
    const totalEl = document.getElementById(`total-${idx}`);

    let qtd = 0;
    if(qtdEl && qtdEl.value) {
        qtd = parseFloat(qtdEl.value.replace(',', '.')) || 0;
    }
    
    let unit = window.lerValorLocal(unitEl);
    let total = window.lerValorLocal(totalEl);
    
    if (origem === 'qtd') {
        if (unit > 0) window.formatarNoElemento(totalEl, qtd * unit);
        else if (total > 0 && qtd > 0) window.formatarNoElemento(unitEl, total / qtd);
    } 
    else if (origem === 'unit') {
        window.formatarNoElemento(totalEl, qtd * unit);
    } 
    else if (origem === 'total') {
        if (qtd > 0) window.formatarNoElemento(unitEl, total / qtd);
    }
    
    window.calcularTotal();
};

window.calcularTotal = function() {
    let subtotal = 0;
    const inputsTotal = document.querySelectorAll('input[name*="[total]"]');
    inputsTotal.forEach(inp => { subtotal += window.lerValorLocal(inp); });
    
    const displaySub = document.getElementById('displaySubtotal');
    if(displaySub) displaySub.innerText = subtotal.toLocaleString('pt-BR', {minimumFractionDigits: 2});

    const acrescimo = window.lerValorLocal(document.getElementById('inputAcrescimo'));
    
    let descValor = 0;
    let descTipo = 'sem';
    
    const inputDescFlask = document.getElementById('valor_desconto_aplicado');
    const inputDescManual = document.getElementById('inputDesconto');
    
    if(inputDescFlask) descValor = window.lerValorLocal(inputDescFlask);
    else if(inputDescManual) descValor = window.lerValorLocal(inputDescManual);

    let radiosTipo = document.getElementsByName('tipo_desconto');
    if(radiosTipo.length === 0) radiosTipo = document.getElementsByName('tipo_desconto_visual');
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

    const elDisplayBase = document.getElementById('displayBase');
    if (elDisplayBase) elDisplayBase.innerText = `R$ ${subtotal.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
    
    const elDisplayAcre = document.getElementById('displayAcrescimo');
    if (elDisplayAcre) elDisplayAcre.innerText = `+ R$ ${acrescimo.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
    
    const elDisplayDesc = document.getElementById('displayDesconto');
    if (elDisplayDesc) elDisplayDesc.innerText = `- R$ ${descontoReais.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
    
    const elDisplayTot = document.getElementById('displayTotal');
    if (elDisplayTot) elDisplayTot.innerText = `R$ ${final.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
    
    const hiddenTotal = document.getElementById('hiddenTotalFinal'); 
    if(hiddenTotal) hiddenTotal.value = final.toFixed(2);
};

window.toggleDesconto = function() {
    let radios = document.getElementsByName('tipo_desconto');
    if(radios.length === 0) radios = document.getElementsByName('tipo_desconto_visual');
    
    let tipo = 'sem';
    for(let r of radios) if(r.checked) tipo = r.value;
    
    const inputManual = document.getElementById('inputDesconto') || document.getElementById('valor_desconto_aplicado');
    
    if(inputManual) {
        if(tipo === 'sem') {
            inputManual.disabled = true;
            inputManual.value = '';
        } else {
            inputManual.disabled = false;
        }
    }
    window.calcularTotal();
};

window.alternarTipoCliente = function(tipo) {
    const areaPf = document.getElementById('campos-pf');
    const areaPj = document.getElementById('campos-pj');
    
    if (!areaPf || !areaPj) return;

    if (tipo === 'PF') {
        areaPf.classList.remove('hidden');
        areaPf.classList.remove('hidden-force');
        areaPj.classList.add('hidden');
        areaPj.classList.add('hidden-force');
        areaPf.querySelectorAll('input').forEach(i => { if(i.name !== 'pf_cpf') i.required = true; });
        areaPj.querySelectorAll('input').forEach(i => i.required = false);
    } else {
        areaPf.classList.add('hidden');
        areaPf.classList.add('hidden-force');
        areaPj.classList.remove('hidden');
        areaPj.classList.remove('hidden-force');
        areaPf.querySelectorAll('input').forEach(i => i.required = false);
        areaPj.querySelectorAll('input').forEach(i => { if(i.name !== 'pj_cnpj') i.required = true; });
    }
};

// --- INICIALIZAÇÃO AO CARREGAR A PÁGINA ---
document.addEventListener('DOMContentLoaded', function() {
    
    const scriptProdutos = document.getElementById('dados-produtos');
    const formMultiplo = document.getElementById('formMultiplo');
    
    if (scriptProdutos) {
        try { PRODUTOS_DISPONIVEIS = JSON.parse(scriptProdutos.textContent); } catch(e) {}
    } else if (formMultiplo && formMultiplo.dataset.produtos) {
        try { PRODUTOS_DISPONIVEIS = JSON.parse(formMultiplo.dataset.produtos); } catch(e) {}
    }

    ['inputAcrescimo', 'inputDesconto', 'valor_desconto_aplicado'].forEach(id => {
        let el = document.getElementById(id);
        if (el) window.aplicarMascaraMoeda(el, window.calcularTotal);
    });

    if(formMultiplo) {
        formMultiplo.addEventListener('submit', function(e) {
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
                alert(`O tamanho total das imagens (${tamanhoAtualMB} MB) excede o limite permitido de ${LIMITE_MB} MB.`);
                return;
            }

            const inputsUnit = document.querySelectorAll('input[name*="[unit]"]');
            if (inputsUnit.length === 0) {
                e.preventDefault();
                alert("Adicione pelo menos um item à venda.");
                return;
            }
            
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

    if(typeof lucide !== 'undefined') lucide.createIcons();
    
    let radioChecked = document.querySelector('input[name="tipo_cliente"]:checked');
    if(radioChecked) {
        window.alternarTipoCliente(radioChecked.value);
    } else {
        window.alternarTipoCliente('PF');
    }
    
    window.adicionarLinha(); 
});