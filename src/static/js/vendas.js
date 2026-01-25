// src/static/js/vendas.js

document.addEventListener('DOMContentLoaded', function() {
    
    // 1. Inicializa Ícones
    if(typeof lucide !== 'undefined') lucide.createIcons();

    // 2. Configura Event Listeners (Ouvintes de Eventos)
    setupEventListeners();

    // 3. Executa estado inicial
    toggleCliente(); 
    atualizarUnidadeECalcular(); 
});

function setupEventListeners() {
    // PF vs PJ
    const radiosTipo = document.querySelectorAll('input[name="tipo_cliente"]');
    radiosTipo.forEach(radio => radio.addEventListener('change', toggleCliente));

    // Inputs que disparam cálculo (Tamanho, Qtd, Acréscimo, Desconto)
    const inputsCalculo = document.querySelectorAll('.input-calc, [name="dim_1"], [name="dim_2"], [name="dim_3"], [name="qtd_pecas"], [name="input_acrescimo"], [name="input_desconto"]');
    inputsCalculo.forEach(input => {
        input.addEventListener('input', calculateAll);
        input.addEventListener('change', calculateAll); // Para inputs type number
    });

    // Selects
    const selectCor = document.getElementById('select-cor');
    if (selectCor) selectCor.addEventListener('change', atualizarUnidadeECalcular);

    const selectMedida = document.getElementById('select-medida');
    if (selectMedida) selectMedida.addEventListener('change', calculateAll);

    // Radio de Tipo de Desconto (R$ ou %)
    const radiosDesconto = document.querySelectorAll('input[name="tipo_desconto"]');
    radiosDesconto.forEach(radio => radio.addEventListener('change', calculateAll));

    // Máscaras
    const inpCpf = document.querySelector('[name="pf_cpf"]');
    const inpCnpj = document.querySelector('[name="pj_cnpj"]');
    const inpTel = document.querySelector('[name="telefone"]');

    if(inpCpf) inpCpf.addEventListener('input', e => mascaraCpf(e.target));
    if(inpCnpj) inpCnpj.addEventListener('input', e => mascaraCnpj(e.target));
    if(inpTel) inpTel.addEventListener('input', e => mascaraTel(e.target));
}

// --- LÓGICA DE NEGÓCIO ---

function toggleCliente() {
    const radioPf = document.querySelector('input[name="tipo_cliente"][value="PF"]');
    // Se não achar o radio (erro de renderização), assume PF por segurança
    const isPf = radioPf ? radioPf.checked : true;
    
    const blocoPf = document.getElementById('bloco-pf');
    const blocoPj = document.getElementById('bloco-pj');
    
    // Inputs obrigatórios de cada bloco
    const inputsPf = blocoPf ? blocoPf.querySelectorAll('input') : [];
    const inputsPj = blocoPj ? blocoPj.querySelectorAll('input') : [];

    if (isPf) {
        if(blocoPf) blocoPf.classList.remove('hidden-force');
        if(blocoPj) blocoPj.classList.add('hidden-force');
        
        inputsPf.forEach(i => i.required = true);
        inputsPj.forEach(i => i.required = false);
    } else {
        if(blocoPf) blocoPf.classList.add('hidden-force');
        if(blocoPj) blocoPj.classList.remove('hidden-force');
        
        inputsPf.forEach(i => i.required = false);
        inputsPj.forEach(i => i.required = true);
    }
}

function atualizarUnidadeECalcular() {
    const selectCor = document.getElementById('select-cor');
    const selectMedida = document.getElementById('select-medida');
    
    if (selectCor && selectCor.selectedIndex >= 0 && selectMedida) {
        const option = selectCor.options[selectCor.selectedIndex];
        const unidadeCadastrada = option.getAttribute('data-unidade'); 
        
        if (unidadeCadastrada) {
            const und = unidadeCadastrada.toLowerCase().trim();
            let encontrou = false;
            
            // Tenta achar a opção no select de medidas
            for (let i = 0; i < selectMedida.options.length; i++) {
                if (selectMedida.options[i].value === und) {
                    selectMedida.selectedIndex = i;
                    encontrou = true;
                    break;
                }
            }
            
            // Se a unidade existe, trava o campo. Se não, deixa livre.
            if (encontrou) {
                selectMedida.classList.add('input-locked');
                // Usamos style pointer-events para garantir bloqueio de clique sem usar 'disabled' (que não envia no form)
                selectMedida.style.pointerEvents = 'none';
            } else {
                selectMedida.classList.remove('input-locked');
                selectMedida.style.pointerEvents = 'auto';
            }
        } else {
            // Opção "Selecione..." ou sem unidade
            selectMedida.classList.remove('input-locked');
            selectMedida.style.pointerEvents = 'auto';
        }
    }
    // Recalcula tudo com a nova unidade
    calculateAll();
}

function calculateAll() {
    // 1. Coleta Valores
    const dim1 = parseFloat(document.querySelector('[name="dim_1"]').value) || 0;
    const dim2 = parseFloat(document.querySelector('[name="dim_2"]').value) || 0;
    const dim3 = parseFloat(document.querySelector('[name="dim_3"]').value) || 0;
    const qtd  = parseFloat(document.querySelector('[name="qtd_pecas"]').value) || 1;
    
    const selectMedida = document.getElementById('select-medida');
    const tipoMedida = selectMedida ? selectMedida.value : 'm2';
    
    const divDim3 = document.getElementById('div-dim-3');
    const displayUnidade = document.getElementById('display-unidade');

    // 2. Calcula Metragem
    let metragem = 0;

    if (tipoMedida === 'm3') {
        if(divDim3) divDim3.classList.remove('hidden-force');
        if(displayUnidade) displayUnidade.innerText = 'm³';
        metragem = dim1 * dim2 * (dim3 > 0 ? dim3 : 1);
    } else {
        if(divDim3) divDim3.classList.add('hidden-force');
        if(displayUnidade) displayUnidade.innerText = 'm²';
        metragem = dim1 * dim2;
    }

    // 3. Atualiza Displays de Metragem
    const elDisplayMetragem = document.getElementById('display-metragem');
    const elInputHidden = document.getElementById('metragem_calculada');
    
    if(elDisplayMetragem) elDisplayMetragem.innerText = metragem.toFixed(2);
    if(elInputHidden) elInputHidden.value = metragem.toFixed(2);

    // 4. Busca Preço
    let precoCor = 0;
    const selectCor = document.getElementById('select-cor');
    if (selectCor && selectCor.selectedIndex >= 0) {
        const option = selectCor.options[selectCor.selectedIndex];
        precoCor = parseFloat(option.getAttribute('data-preco')) || 0;
    }

    // 5. Calcula Financeiro
    const valorBase = (metragem * precoCor) * qtd;
    const acrescimo = parseFloat(document.querySelector('[name="input_acrescimo"]').value) || 0;
    const valorInputDesc = parseFloat(document.querySelector('[name="input_desconto"]').value) || 0;
    
    // Verifica tipo de desconto (R$ ou %)
    const tipoDescRadio = document.querySelector('input[name="tipo_desconto"]:checked');
    const tipoDesc = tipoDescRadio ? tipoDescRadio.value : 'real';
    
    // Atualiza ícone visualmente
    const prefixoDesc = document.getElementById('prefixo-desconto');
    if(prefixoDesc) prefixoDesc.innerText = (tipoDesc === 'perc') ? '%' : 'R$';

    let descontoReais = 0;
    const subtotal = valorBase + acrescimo;

    if (tipoDesc === 'perc') {
        descontoReais = subtotal * (valorInputDesc / 100);
    } else {
        descontoReais = valorInputDesc;
    }

    let final = subtotal - descontoReais;
    if (final < 0) final = 0;

    // 6. Atualiza Resumo Final
    const elResumoBase = document.getElementById('resumo-base');
    const elResumoTotal = document.getElementById('resumo-total');

    if(elResumoBase) elResumoBase.innerText = valorBase.toFixed(2);
    if(elResumoTotal) elResumoTotal.innerText = final.toFixed(2);
}

// --- MÁSCARAS ---

function mascaraCpf(input){
    let v = input.value.replace(/\D/g,"");
    v=v.replace(/(\d{3})(\d)/,"$1.$2");
    v=v.replace(/(\d{3})(\d)/,"$1.$2");
    v=v.replace(/(\d{3})(\d{1,2})$/,"$1-$2");
    input.value = v.substring(0, 14);
}

function mascaraCnpj(input){
    let v = input.value.replace(/\D/g,"");
    v=v.replace(/^(\d{2})(\d)/,"$1.$2");
    v=v.replace(/^(\d{2})\.(\d{3})(\d)/,"$1.$2.$3");
    v=v.replace(/\.(\d{3})(\d)/,".$1/$2");
    v=v.replace(/(\d{4})(\d)/,"$1-$2");
    input.value = v.substring(0, 18);
}

function mascaraTel(input){
    let v = input.value.replace(/\D/g,"");
    v=v.replace(/^(\d{2})(\d)/,"($1) $2");
    v=v.replace(/(\d{5})(\d)/,"$1-$2");
    input.value = v.substring(0, 15);
}