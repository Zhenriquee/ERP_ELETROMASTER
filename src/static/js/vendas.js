// src/static/js/vendas.js

document.addEventListener('DOMContentLoaded', function() {
    if(typeof lucide !== 'undefined') lucide.createIcons();
    setupEventListeners();
    
    if(document.querySelector('input[name="tipo_cliente"]:checked')) {
        window.alternarTipoCliente(document.querySelector('input[name="tipo_cliente"]:checked').value);
    } else {
        window.alternarTipoCliente('PF');
    }
    
    setTimeout(atualizarUnidadeECalcular, 100);
});

window.aplicarMascaraMoeda = function(input) {
    if(!input) return;
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
            return;
        }
        v = (parseFloat(v) / 100).toFixed(2);
        v = v.replace('.', ',');
        v = v.replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1.');
        e.target.value = v;
    });
}

window.lerValorMonetario = function(id) {
    const el = document.getElementById(id);
    if (!el || !el.value) return 0;
    let valStr = el.value.replace(/\./g, '').replace(',', '.');
    return parseFloat(valStr) || 0;
}

window.lerDecimalGenerico = function(id) {
    const el = document.getElementById(id);
    if (!el || !el.value) return 0;
    return parseFloat(el.value.replace(',', '.')) || 0;
}

function setupEventListeners() {
    const inputsMonetarios = ['valor_acrescimo', 'inputDesconto', 'valor_desconto_aplicado'];
    inputsMonetarios.forEach(id => {
        window.aplicarMascaraMoeda(document.getElementById(id));
    });

    const formVenda = document.getElementById('formVenda');
    if (formVenda) {
        formVenda.addEventListener('submit', function() {
            inputsMonetarios.forEach(id => {
                const el = document.getElementById(id);
                if (el && el.value) el.value = el.value.replace(/\./g, '').replace(',', '.');
            });
            ['dimensao_1', 'dimensao_2', 'dimensao_3', 'quantidade_pecas'].forEach(id => {
                const el = document.getElementById(id);
                if (el && el.value) el.value = el.value.replace(',', '.');
            });
        });
    }

    const inputsCalculo = document.querySelectorAll(
        '#dimensao_1, #dimensao_2, #dimensao_3, #quantidade_pecas, #valor_acrescimo, #inputDesconto, #valor_desconto_aplicado'
    );
    inputsCalculo.forEach(input => {
        input.addEventListener('input', window.calcularTotal);
        input.addEventListener('change', window.calcularTotal);
    });

    const selectProduto = document.getElementById('select-produto');
    if (selectProduto) selectProduto.addEventListener('change', atualizarUnidadeECalcular);

    const selectMedida = document.getElementById('select-medida');
    if (selectMedida) selectMedida.addEventListener('change', window.calcularTotal);

    configurarMascaras();
}

function atualizarUnidadeECalcular() {
    const selectProduto = document.getElementById('select-produto');
    const selectMedida = document.getElementById('select-medida');
    
    let avisoErro = document.getElementById('aviso-sem-preco');
    if (!avisoErro && selectMedida) {
        avisoErro = document.createElement('div');
        avisoErro.id = 'aviso-sem-preco';
        avisoErro.className = 'text-red-600 text-xs mt-1 font-bold hidden';
        avisoErro.innerText = 'Produto sem preço cadastrado para esta unidade!';
        selectMedida.parentNode.appendChild(avisoErro);
    }
    
    if (selectProduto && selectProduto.selectedIndex >= 0 && selectMedida) {
        const option = selectProduto.options[selectProduto.selectedIndex];
        
        const precoM2 = parseFloat(option.getAttribute('data-m2')) || 0;
        const precoM3 = parseFloat(option.getAttribute('data-m3')) || 0;
        
        const optionM2 = selectMedida.querySelector('option[value="m2"]');
        const optionM3 = selectMedida.querySelector('option[value="m3"]');

        selectMedida.style.pointerEvents = 'auto'; 
        selectMedida.classList.remove('bg-gray-100', 'text-gray-400', 'border-red-500', 'bg-red-50'); 
        if(avisoErro) avisoErro.classList.add('hidden');
        if(optionM2) optionM2.disabled = false;
        if(optionM3) optionM3.disabled = false;

        if (precoM2 > 0 && precoM3 > 0) {
            // Escolhe livremente
        } else if (precoM2 > 0) {
            selectMedida.value = 'm2';
            if(optionM3) optionM3.disabled = true; 
        } else if (precoM3 > 0) {
            selectMedida.value = 'm3';
            if(optionM2) optionM2.disabled = true;
        } else {
            selectMedida.value = 'm2';
            selectMedida.style.pointerEvents = 'none';
            selectMedida.classList.add('bg-red-50', 'text-gray-400', 'border-red-500');
            if(avisoErro) avisoErro.classList.remove('hidden');
        }
    }
    window.calcularTotal();
}

window.calcularTotal = function() {
    const d1 = window.lerDecimalGenerico('dimensao_1');
    const d2 = window.lerDecimalGenerico('dimensao_2');
    const d3 = window.lerDecimalGenerico('dimensao_3');
    const qtd = window.lerDecimalGenerico('quantidade_pecas') || 1;
    
    const selectMedida = document.getElementById('select-medida');
    const tipoMedida = selectMedida ? selectMedida.value : 'm2';
    
    const divDim3 = document.getElementById('div-dim-3');
    const displayUnidade = document.getElementById('display-unidade');

    let precoUnitario = 0;
    const selectProduto = document.getElementById('select-produto');
    
    if (selectProduto && selectProduto.selectedIndex >= 0) {
        const option = selectProduto.options[selectProduto.selectedIndex];
        const pM2 = parseFloat(option.getAttribute('data-m2')) || 0;
        const pM3 = parseFloat(option.getAttribute('data-m3')) || 0;
        
        if (tipoMedida === 'm3') {
            precoUnitario = pM3;
            if(divDim3) divDim3.classList.remove('hidden-force');
            if(displayUnidade) displayUnidade.innerText = 'm³';
        } else {
            precoUnitario = pM2;
            if(divDim3) divDim3.classList.add('hidden-force');
            if(displayUnidade) displayUnidade.innerText = 'm²';
        }
    }

    let metragem = 0;
    if (tipoMedida === 'm3') {
        metragem = d1 * d2 * (d3 > 0 ? d3 : 0) * qtd;
    } else {
        metragem = d1 * d2 * qtd;
    }

    const elDisplayMet = document.getElementById('display-metragem');
    const elInputMet = document.getElementById('metragem_total'); 
    
    const casas = (tipoMedida === 'm3') ? 3 : 2;
    const metragemFmt = metragem.toFixed(casas).replace('.', ',');

    if(elDisplayMet) elDisplayMet.innerText = metragemFmt;
    if(elInputMet) elInputMet.value = metragemFmt;

    const valorBase = metragem * precoUnitario;
    
    const elValorBase = document.getElementById('valor_base');
    const elResumoBase = document.getElementById('resumo-base');
    
    if(elValorBase) elValorBase.value = valorBase.toFixed(2).replace('.', ',');
    if(elResumoBase) elResumoBase.innerText = valorBase.toFixed(2).replace('.', ',');

    const acrescimo = window.lerValorMonetario('valor_acrescimo');
    
    let inputDescManual = document.getElementById('inputDesconto');
    let inputDescFlask = document.getElementById('valor_desconto_aplicado');
    let valorInputDesc = inputDescFlask ? window.lerValorMonetario('valor_desconto_aplicado') : window.lerValorMonetario('inputDesconto');
    
    let tipoDescRadio = document.querySelector('input[name="tipo_desconto"]:checked');
    if(!tipoDescRadio) tipoDescRadio = document.querySelector('input[name="tipo_desconto_visual"]:checked');
    const tipoDesc = tipoDescRadio ? tipoDescRadio.value : 'sem';
    
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

    const elResumoTotal = document.getElementById('resumo-total');
    const elInputFinal = document.getElementById('valor_final');

    if(elResumoTotal) elResumoTotal.innerText = final.toFixed(2).replace('.', ',');
    if(elInputFinal) elInputFinal.value = final.toFixed(2).replace('.', ',');
}

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
    // Busca os IDs corretos que estão no form_cliente.html
    const areaPf = document.getElementById('campos-pf') || document.getElementById('bloco-pf');
    const areaPj = document.getElementById('campos-pj') || document.getElementById('bloco-pj');
    
    if (!areaPf || !areaPj) return;

    if (tipo === 'PF') {
        areaPf.classList.remove('hidden');
        areaPf.classList.remove('hidden-force');
        areaPj.classList.add('hidden');
        areaPj.classList.add('hidden-force');
        // Ajusta a obrigatoriedade dos campos
        areaPf.querySelectorAll('input').forEach(i => { if(i.name !== 'pf_cpf') i.required = true; });
        areaPj.querySelectorAll('input').forEach(i => i.required = false);
    } else {
        areaPf.classList.add('hidden');
        areaPf.classList.add('hidden-force');
        areaPj.classList.remove('hidden');
        areaPj.classList.remove('hidden-force');
        // Ajusta a obrigatoriedade dos campos
        areaPf.querySelectorAll('input').forEach(i => i.required = false);
        areaPj.querySelectorAll('input').forEach(i => { if(i.name !== 'pj_cnpj') i.required = true; });
    }
};

function configurarMascaras() {
    const inpCpf = document.querySelector('[name="pf_cpf"]');
    const inpCnpj = document.querySelector('[name="pj_cnpj"]');
    const inpTel = document.querySelector('[name="telefone"]');

    if(inpCpf) inpCpf.addEventListener('input', e => {
        let v = e.target.value.replace(/\D/g,""); 
        if (v.length > 11) v = v.substring(0, 11); 
        v=v.replace(/(\d{3})(\d)/,"$1.$2");
        v=v.replace(/(\d{3})(\d)/,"$1.$2");
        v=v.replace(/(\d{3})(\d{1,2})$/,"$1-$2");
        e.target.value = v;
    });

    if(inpCnpj) inpCnpj.addEventListener('input', e => {
        let v = e.target.value.replace(/\D/g,"");
        v=v.replace(/^(\d{2})(\d)/,"$1.$2");
        v=v.replace(/^(\d{2})\.(\d{3})(\d)/,"$1.$2.$3");
        v=v.replace(/\.(\d{3})(\d)/,".$1/$2");
        v=v.replace(/(\d{4})(\d)/,"$1-$2");
        e.target.value = v.substring(0, 18);
    });

    if(inpTel) inpTel.addEventListener('input', e => {
        let v = e.target.value.replace(/\D/g,"");
        v=v.replace(/^(\d{2})(\d)/,"($1) $2");
        v=v.replace(/(\d{5})(\d)/,"$1-$2");
        e.target.value = v.substring(0, 15);
    });
}