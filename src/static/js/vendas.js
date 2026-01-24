document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1. LÓGICA PF vs PJ (Toggle) ---
    // Recupera os elementos
    const radios = document.querySelectorAll('input[name="tipo_cliente"]');
    const blocoPf = document.getElementById('bloco-pf');
    const blocoPj = document.getElementById('bloco-pj');

    // Campos obrigatórios que precisamos ativar/desativar
    // (Ajuste os IDs conforme seu formulário real no HTML)
    const inputsPf = [
        document.querySelector('[name="pf_nome"]'),
        document.querySelector('[name="pf_cpf"]'),
        document.querySelector('[name="telefone"]')
    ];
    const inputsPj = [
        document.querySelector('[name="pj_fantasia"]'),
        document.querySelector('[name="pj_solicitante"]'),
        document.querySelector('[name="pj_cnpj"]')
    ];

    function toggleCliente() {
        // Descobre qual radio está marcado
        let tipoSelecionado = 'PF';
        radios.forEach(r => {
            if (r.checked) tipoSelecionado = r.value;
        });

        if (tipoSelecionado === 'PJ') {
            // Mostra PJ, Esconde PF
            if(blocoPf) blocoPf.classList.add('hidden-force');
            if(blocoPj) blocoPj.classList.remove('hidden-force');
            
            // Gerencia 'Required' para validação HTML5 não falhar em campos ocultos
            inputsPf.forEach(el => { if(el) el.required = false; });
            inputsPj.forEach(el => { if(el) el.required = true; });

        } else {
            // Mostra PF, Esconde PJ
            if(blocoPf) blocoPf.classList.remove('hidden-force');
            if(blocoPj) blocoPj.classList.add('hidden-force');

            inputsPf.forEach(el => { if(el) el.required = true; });
            inputsPj.forEach(el => { if(el) el.required = false; });
        }
    }

    // Adiciona evento de mudança nos radios
    radios.forEach(r => r.addEventListener('change', toggleCliente));
    
    // Inicializa o estado correto ao carregar a página
    toggleCliente();


    // --- 2. LÓGICA DE CÁLCULO AUTOMÁTICO ---
    
    // Mapeia todos os inputs que afetam o preço
    const inputsCalculo = document.querySelectorAll('.input-calc, #select-cor, #select-medida, [name="input_acrescimo"], [name="input_desconto"]');

    function calculateAll() {
        // 1. Pegar valores (usando 0 se vazio)
        const dim1 = parseFloat(document.querySelector('[name="dim_1"]').value) || 0;
        const dim2 = parseFloat(document.querySelector('[name="dim_2"]').value) || 0;
        const dim3 = parseFloat(document.querySelector('[name="dim_3"]').value) || 0;
        const qtd  = parseFloat(document.querySelector('[name="qtd_pecas"]').value) || 1;
        
        const tipoMedida = document.getElementById('select-medida').value;
        
        // Controle de visibilidade do campo dimensão 3 (Profundidade)
        const divDim3 = document.getElementById('div-dim-3');
        const displayUnidade = document.getElementById('display-unidade');
        
        let metragemTotal = 0;

        if (tipoMedida === 'm3') {
            if(divDim3) divDim3.classList.remove('hidden-force');
            if(displayUnidade) displayUnidade.innerText = 'm³';
            metragemTotal = dim1 * dim2 * (dim3 > 0 ? dim3 : 1);
        } else {
            if(divDim3) divDim3.classList.add('hidden-force');
            if(displayUnidade) displayUnidade.innerText = 'm²';
            metragemTotal = dim1 * dim2;
        }

        // Atualiza displays de metragem
        const elDisplayMetragem = document.getElementById('display-metragem');
        const elInputHidden = document.getElementById('metragem_calculada');
        
        if(elDisplayMetragem) elDisplayMetragem.innerText = metragemTotal.toFixed(2);
        if(elInputHidden) elInputHidden.value = metragemTotal.toFixed(2);

        // 2. Pegar Preço da Cor
        let precoBaseCor = 0;
        const selectCor = document.getElementById('select-cor');
        const corIdSelecionada = parseInt(selectCor.value);
        
        // Tenta achar no objeto global DB_CORES (injetado no HTML)
        if (window.DB_CORES) {
            const corEncontrada = window.DB_CORES.find(c => c.id === corIdSelecionada);
            if (corEncontrada) {
                precoBaseCor = parseFloat(corEncontrada.preco);
            }
        }

        // 3. Calcular Totais Financeiros
        // Fórmula: (Metragem * PreçoCor) * Quantidade
        let valorServicoBase = (metragemTotal * precoBaseCor) * qtd;

        const acrescimo = parseFloat(document.querySelector('[name="input_acrescimo"]').value) || 0;
        const desconto = parseFloat(document.querySelector('[name="input_desconto"]').value) || 0;

        let valorFinal = valorServicoBase + acrescimo - desconto;
        if (valorFinal < 0) valorFinal = 0;

        // 4. Atualizar na Tela
        const elResumoBase = document.getElementById('resumo-base');
        const elResumoTotal = document.getElementById('resumo-total');

        if(elResumoBase) elResumoBase.innerText = valorServicoBase.toFixed(2);
        if(elResumoTotal) elResumoTotal.innerText = valorFinal.toFixed(2);
    }

    // Adiciona o evento 'input' e 'change' a todos os campos mapeados
    inputsCalculo.forEach(el => {
        el.addEventListener('input', calculateAll);
        el.addEventListener('change', calculateAll);
    });

    // Rodar cálculo inicial (caso venha preenchido do backend em edição)
    calculateAll();
    
    // --- 3. MÁSCARAS (Opcional, mas recomendado) ---
    const cpfInput = document.querySelector('[name="pf_cpf"]');
    if(cpfInput) {
        cpfInput.addEventListener('input', function(e) {
            let v = e.target.value.replace(/\D/g, "");
            if(v.length > 11) v = v.slice(0, 11);
            e.target.value = v.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, "$1.$2.$3-$4");
        });
    }
});