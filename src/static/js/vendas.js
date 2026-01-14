document.addEventListener('DOMContentLoaded', function() {
    
    // ==========================================
    // 1. INICIALIZAÇÃO E VARIÁVEIS GLOBAIS
    // ==========================================
    let currentStep = 1;
    const totalSteps = 6;
    
    const btnNext = document.getElementById('btn-next');
    const btnPrev = document.getElementById('btn-prev');
    const btnSubmit = document.getElementById('btn-submit');
    const steps = document.querySelectorAll('.wizard-step');
    const indicators = document.querySelectorAll('.step-indicator');

    // ==========================================
    // 2. CONTROLE DO WIZARD (NAVEGAÇÃO)
    // ==========================================
    function updateWizard() {
        // Mostrar/Esconder Steps
        steps.forEach(step => {
            if(parseInt(step.dataset.step) === currentStep) {
                step.classList.remove('hidden');
            } else {
                step.classList.add('hidden');
            }
        });

        // Atualizar Indicadores (Bolinhas do topo)
        indicators.forEach(ind => {
            const stepNum = parseInt(ind.dataset.step);
            ind.classList.remove('bg-navy-900', 'text-white', 'border-navy-900', 'bg-green-500', 'border-green-500');
            
            if (stepNum === currentStep) {
                ind.classList.add('bg-navy-900', 'text-white', 'border-navy-900');
            } else if (stepNum < currentStep) {
                ind.classList.add('bg-green-500', 'text-white', 'border-green-500'); // Já passou
            } else {
                ind.classList.add('bg-gray-100'); // Futuro
            }
        });

        // Controle dos Botões
        btnPrev.disabled = currentStep === 1;
        
        if (currentStep === totalSteps) {
            btnNext.classList.add('hidden');
            btnSubmit.classList.remove('hidden');
            preencherRevisao(); // Popula o resumo final ao chegar na última tela
        } else {
            btnNext.classList.remove('hidden');
            btnSubmit.classList.add('hidden');
        }
    }

    // Botão Próximo
    if (btnNext) {
        btnNext.addEventListener('click', () => {
            if(validateStep(currentStep)) {
                currentStep++;
                updateWizard();
                calculateAll(); // Recalcula valores ao avançar
            }
        });
    }

    // Botão Voltar
    if (btnPrev) {
        btnPrev.addEventListener('click', () => {
            currentStep--;
            updateWizard();
        });
    }

    // Validação Simples (Campos Required)
    function validateStep(step) {
        const currentStepDiv = document.querySelector(`.wizard-step[data-step="${step}"]`);
        // Seleciona inputs visíveis que são obrigatórios
        const inputs = currentStepDiv.querySelectorAll('input:not(.hidden), select, textarea');
        let isValid = true;

        inputs.forEach(inp => {
            // Checa se é required e está vazio (ignora se estiver escondido via classe hidden)
            if (inp.required && !inp.value && !inp.closest('.hidden')) {
                inp.classList.add('border-red-500', 'ring-1', 'ring-red-500');
                isValid = false;
            } else {
                inp.classList.remove('border-red-500', 'ring-1', 'ring-red-500');
            }
        });

        if (!isValid) {
            // Feedback visual simples (pode ser melhorado com Toast)
            const flashArea = document.querySelector('header'); // Tenta achar um lugar para scrollar
            if(flashArea) flashArea.scrollIntoView({behavior: 'smooth'});
            alert('Por favor, preencha os campos obrigatórios marcados em vermelho.');
        }
        return isValid;
    }

    // ==========================================
    // 3. LÓGICA DE NEGÓCIO (PF vs PJ)
    // ==========================================
    const radiosTipo = document.getElementsByName('tipo_cliente');
    const blocoPf = document.getElementById('bloco-pf');
    const blocoPj = document.getElementById('bloco-pj');
    
    function toggleCliente() {
        let tipo = 'PF';
        for(let r of radiosTipo) if(r.checked) tipo = r.value;
        
        if (tipo === 'PF') {
            blocoPf.classList.remove('hidden');
            blocoPj.classList.add('hidden');
            
            // Ajusta obrigatoriedade (HTML5 validation)
            setRequired(blocoPj, false);
            setRequired(blocoPf, true);
        } else {
            blocoPf.classList.add('hidden');
            blocoPj.classList.remove('hidden');

            setRequired(blocoPf, false);
            setRequired(blocoPj, true);
        }
    }

    function setRequired(container, isRequired) {
        const inputs = container.querySelectorAll('input');
        inputs.forEach(inp => {
            // Apenas marca como required se o campo tiver um label com * (convenção visual)
            // Ou for explicitamente um campo chave
            if (inp.name.includes('nome') || inp.name.includes('fantasia') || inp.name.includes('solicitante')) {
                inp.required = isRequired;
            }
        });
    }

    radiosTipo.forEach(r => r.addEventListener('change', toggleCliente));
    

    // ==========================================
    // 4. LÓGICA DE CÁLCULOS (METRAGEM E PREÇO)
    // ==========================================
    const selMedida = document.getElementById('select-medida');
    const divDim3 = document.getElementById('div-dim-3');
    const displayUnidade = document.getElementById('display-unidade');
    const inputsCalc = document.querySelectorAll('.input-calc, #select-cor, #select-medida, [name="dim_1"], [name="dim_2"], [name="dim_3"]');

    // Troca m2 / m3
    if (selMedida) {
        selMedida.addEventListener('change', () => {
            if(selMedida.value === 'm3') {
                divDim3.classList.remove('hidden');
                displayUnidade.innerText = 'm³';
            } else {
                divDim3.classList.add('hidden');
                displayUnidade.innerText = 'm²';
                const dim3 = document.querySelector('[name="dim_3"]');
                if(dim3) dim3.value = 0;
            }
            calculateAll();
        });
    }

    // Listeners para recalcular em tempo real
    inputsCalc.forEach(inp => inp.addEventListener('input', calculateAll));
    inputsCalc.forEach(inp => inp.addEventListener('change', calculateAll));

    function calculateAll() {
        // 1. Pegar Dimensões
        const dim1 = parseFloat(document.querySelector('[name="dim_1"]').value) || 0;
        const dim2 = parseFloat(document.querySelector('[name="dim_2"]').value) || 0;
        const dim3 = parseFloat(document.querySelector('[name="dim_3"]').value) || 0;
        const qtd = parseInt(document.querySelector('[name="qtd_pecas"]').value) || 1;
        
        // 2. Calcular Metragem
        let metragem = 0;
        if(selMedida.value === 'm3') {
            metragem = dim1 * dim2 * (dim3 > 0 ? dim3 : 1);
        } else {
            metragem = dim1 * dim2;
        }
        
        // Atualiza tela e campo hidden
        const elDisplayMetragem = document.getElementById('display-metragem');
        const elHiddenMetragem = document.querySelector('[name="metragem_calculada"]');
        if(elDisplayMetragem) elDisplayMetragem.innerText = metragem.toFixed(2);
        if(elHiddenMetragem) elHiddenMetragem.value = metragem;

        // 3. Pegar Preço da Cor (Vem do JSON Global CORES_DB)
        // Se CORES_DB não estiver definido (erro de carga), assume lista vazia
        const dbCores = (typeof CORES_DB !== 'undefined') ? CORES_DB : [];
        const corId = parseInt(document.getElementById('select-cor').value);
        const corObj = dbCores.find(c => c.id === corId);
        const precoCor = corObj ? corObj.preco : 0;
        
        const elCorPrecoBase = document.getElementById('cor-preco-base');
        if(elCorPrecoBase) elCorPrecoBase.innerText = precoCor.toFixed(2);

        // 4. Calcular Valor Base
        const valorBase = metragem * qtd * precoCor;
        
        // 5. Calcular Desconto
        let desconto = 0;
        let tipoDesc = 'sem';
        const radioDesc = document.querySelector('input[name="tipo_desconto"]:checked');
        if(radioDesc) tipoDesc = radioDesc.value;

        const valDescInput = parseFloat(document.querySelector('[name="input_desconto"]').value) || 0;

        if (tipoDesc === 'perc') {
            desconto = valorBase * (valDescInput / 100);
        } else if (tipoDesc === 'real') {
            desconto = valDescInput;
        }

        // Evitar valor negativo
        let valorFinal = valorBase - desconto;
        if (valorFinal < 0) valorFinal = 0;

        // 6. Atualizar Resumo Financeiro na UI
        updateText('resumo-preco-unit', precoCor.toFixed(2));
        updateText('resumo-metragem', `${metragem.toFixed(2)} ${selMedida.value} (x${qtd} pçs)`);
        updateText('resumo-base', valorBase.toFixed(2));
        updateText('resumo-desconto', desconto.toFixed(2));
        updateText('resumo-total', valorFinal.toFixed(2));

        // 7. Alerta de Desconto Alto (>15%)
        const percReal = valorBase > 0 ? (desconto / valorBase) : 0;
        const alertDesc = document.getElementById('alert-desconto');
        if (alertDesc) {
            if (percReal > 0.15) alertDesc.classList.remove('hidden');
            else alertDesc.classList.add('hidden');
        }
    }

    function updateText(id, val) {
        const el = document.getElementById(id);
        if(el) el.innerText = val;
    }

    // ==========================================
    // 5. PREENCHER TELA DE REVISÃO
    // ==========================================
    window.preencherRevisao = function() {
        const tipo = document.querySelector('input[name="tipo_cliente"]:checked').value;
        let nome = '';
        let solicitante = '-';
        
        if (tipo === 'PF') {
            nome = document.querySelector('[name="pf_nome"]').value;
        } else {
            nome = document.querySelector('[name="pj_fantasia"]').value;
            solicitante = document.querySelector('[name="pj_solicitante"]').value;
        }

        const servico = document.querySelector('[name="descricao_servico"]').value;
        const total = document.getElementById('resumo-total').innerText;
        
        updateText('rev-cliente', nome);
        updateText('rev-solicitante', solicitante);
        updateText('rev-servico', servico);
        updateText('rev-total', total);
    }

    // Inicialização
    toggleCliente(); // Define estado inicial PF/PJ
    updateWizard();  // Define estado inicial do Wizard
});