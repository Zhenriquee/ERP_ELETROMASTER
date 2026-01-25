document.addEventListener('DOMContentLoaded', function() {
    if(typeof lucide !== 'undefined') lucide.createIcons();
    setupEventListeners();
    toggleCliente(); 
    
    // Pequeno delay para garantir carregamento
    setTimeout(atualizarUnidadeECalcular, 100);
});

function setupEventListeners() {
    // Tipo de Cliente
    const radiosTipo = document.querySelectorAll('input[name="tipo_cliente"]');
    radiosTipo.forEach(radio => radio.addEventListener('change', toggleCliente));

    // Inputs de Cálculo (Dimensões, Qtd, Valores)
    // Usando os IDs corretos do novo formulário
    const inputsCalculo = document.querySelectorAll(
        '#dimensao_1, #dimensao_2, #dimensao_3, #quantidade_pecas, #valor_acrescimo, #valor_desconto_aplicado'
    );
    inputsCalculo.forEach(input => {
        input.addEventListener('input', calculateAll);
        input.addEventListener('change', calculateAll);
    });

    // Selects (Cor e Medida)
    const selectCor = document.getElementById('select-cor');
    if (selectCor) selectCor.addEventListener('change', atualizarUnidadeECalcular);

    const selectMedida = document.getElementById('select-medida');
    if (selectMedida) selectMedida.addEventListener('change', calculateAll);

    // Tipo de Desconto
    const radiosDesconto = document.querySelectorAll('input[name="tipo_desconto"]');
    radiosDesconto.forEach(radio => radio.addEventListener('change', calculateAll));

    configurarMascaras();
}

// --- LÓGICA DE UNIDADE E BLOQUEIO (CORRIGIDA) ---

function atualizarUnidadeECalcular() {
    const selectCor = document.getElementById('select-cor');
    const selectMedida = document.getElementById('select-medida');
    
    // Cria aviso de erro dinamicamente se não existir
    let avisoErro = document.getElementById('aviso-sem-preco');
    if (!avisoErro && selectMedida) {
        avisoErro = document.createElement('div');
        avisoErro.id = 'aviso-sem-preco';
        avisoErro.className = 'text-red-600 text-xs mt-1 font-bold hidden';
        avisoErro.innerText = 'Produto sem preço cadastrado!';
        selectMedida.parentNode.appendChild(avisoErro);
    }
    
    if (selectCor && selectCor.selectedIndex >= 0 && selectMedida) {
        const option = selectCor.options[selectCor.selectedIndex];
        
        // Pega os preços (convertendo para número)
        // Se for vazio ou nulo, vira 0
        const precoM2 = parseFloat(option.getAttribute('data-m2')) || 0;
        const precoM3 = parseFloat(option.getAttribute('data-m3')) || 0;
        
        const optionM2 = selectMedida.querySelector('option[value="m2"]');
        const optionM3 = selectMedida.querySelector('option[value="m3"]');

        // 1. LIMPEZA (Reseta para estado padrão habilitado)
        selectMedida.style.pointerEvents = 'auto'; 
        selectMedida.classList.remove('bg-gray-100', 'text-gray-400', 'border-red-500', 'bg-red-50'); 
        if(avisoErro) avisoErro.classList.add('hidden');
        if(optionM2) optionM2.disabled = false;
        if(optionM3) optionM3.disabled = false;

        // 2. REGRAS DE BLOQUEIO
        if (precoM2 > 0 && precoM3 > 0) {
            // CASO A: Tem os dois -> Usuário escolhe livremente
            
        } else if (precoM2 > 0) {
            // CASO B: Só tem M2 -> Força M2 e desabilita M3 na lista
            selectMedida.value = 'm2';
            if(optionM3) optionM3.disabled = true; 
            
        } else if (precoM3 > 0) {
            // CASO C: Só tem M3 -> Força M3 e desabilita M2 na lista
            selectMedida.value = 'm3';
            if(optionM2) optionM2.disabled = true;

        } else {
            // CASO D: Nenhum preço (ex: "Preto Fosco" sem valor) -> BLOQUEIA TUDO
            selectMedida.value = 'm2'; // Valor padrão dummy
            selectMedida.style.pointerEvents = 'none'; // Impede clique
            selectMedida.classList.add('bg-red-50', 'text-gray-400', 'border-red-500');
            if(avisoErro) avisoErro.classList.remove('hidden');
        }
    }
    
    calculateAll();
}

function calculateAll() {
    // 1. Pega valores dos inputs (com IDs corretos)
    const d1 = parseFloat(document.getElementById('dimensao_1')?.value) || 0;
    const d2 = parseFloat(document.getElementById('dimensao_2')?.value) || 0;
    const d3 = parseFloat(document.getElementById('dimensao_3')?.value) || 0;
    const qtd = parseFloat(document.getElementById('quantidade_pecas')?.value) || 1;
    
    const selectMedida = document.getElementById('select-medida');
    const tipoMedida = selectMedida ? selectMedida.value : 'm2';
    
    // Controle de visibilidade da Profundidade
    const divDim3 = document.getElementById('div-dim-3');
    const displayUnidade = document.getElementById('display-unidade');

    // 2. Define Preço Unitário
    let precoUnitario = 0;
    const selectCor = document.getElementById('select-cor');
    
    if (selectCor && selectCor.selectedIndex >= 0) {
        const option = selectCor.options[selectCor.selectedIndex];
        const pM2 = parseFloat(option.getAttribute('data-m2')) || 0;
        const pM3 = parseFloat(option.getAttribute('data-m3')) || 0;
        
        if (tipoMedida === 'm3') {
            precoUnitario = pM3;
            // Se é M3, precisa mostrar campo de profundidade
            if(divDim3) divDim3.classList.remove('hidden-force');
            if(displayUnidade) displayUnidade.innerText = 'm³';
        } else {
            precoUnitario = pM2;
            // Se é M2, esconde profundidade
            if(divDim3) divDim3.classList.add('hidden-force');
            if(displayUnidade) displayUnidade.innerText = 'm²';
        }
    }

    // 3. Calcula Metragem Total
    let metragem = 0;
    if (tipoMedida === 'm3') {
        // Cúbico: Altura * Largura * Profundidade * Qtd
        // Assumindo que d3 é obrigatório para M3. Se for 0, resultado é 0.
        metragem = d1 * d2 * (d3 > 0 ? d3 : 0) * qtd;
    } else {
        // Quadrado: Altura * Largura * Qtd
        metragem = d1 * d2 * qtd;
    }

    // 4. Atualiza tela
    const elDisplayMet = document.getElementById('display-metragem');
    const elInputMet = document.getElementById('metragem_total'); 
    
    const casas = (tipoMedida === 'm3') ? 3 : 2;
    const metragemFmt = metragem.toFixed(casas).replace('.', ',');

    if(elDisplayMet) elDisplayMet.innerText = metragemFmt;
    if(elInputMet) elInputMet.value = metragemFmt;

    // 5. Calcula Financeiro
    const valorBase = metragem * precoUnitario;
    
    const elValorBase = document.getElementById('valor_base');
    const elResumoBase = document.getElementById('resumo-base');
    
    if(elValorBase) elValorBase.value = valorBase.toFixed(2).replace('.', ',');
    if(elResumoBase) elResumoBase.innerText = valorBase.toFixed(2).replace('.', ',');

    // Acréscimos e Descontos
    const acrescimo = parseFloat(document.getElementById('valor_acrescimo')?.value) || 0;
    const valorInputDesc = parseFloat(document.getElementById('valor_desconto_aplicado')?.value) || 0;
    
    const tipoDescRadio = document.querySelector('input[name="tipo_desconto"]:checked');
    const tipoDesc = tipoDescRadio ? tipoDescRadio.value : 'real';
    
    // Ícone do desconto
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

// --- UTILITÁRIOS ---

function toggleCliente() {
    const radioPf = document.querySelector('input[name="tipo_cliente"][value="PF"]');
    const isPf = radioPf ? radioPf.checked : true;
    const blocoPf = document.getElementById('bloco-pf');
    const blocoPj = document.getElementById('bloco-pj');
    
    if (isPf) {
        if(blocoPf) blocoPf.classList.remove('hidden-force');
        if(blocoPj) blocoPj.classList.add('hidden-force');
    } else {
        if(blocoPf) blocoPf.classList.add('hidden-force');
        if(blocoPj) blocoPj.classList.remove('hidden-force');
    }
}

function configurarMascaras() {
    const inpCpf = document.querySelector('[name="pf_cpf"]');
    const inpCnpj = document.querySelector('[name="pj_cnpj"]');
    const inpTel = document.querySelector('[name="telefone"]');

    if(inpCpf) inpCpf.addEventListener('input', e => {
        let v = e.target.value.replace(/\D/g,""); // Remove tudo que não é dígito
        
        if (v.length > 11) v = v.substring(0, 11); // Trava em 11 números

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