document.addEventListener('DOMContentLoaded', function() {
    
    // ==========================================
    // 0. BLOQUEIO DE SUBMIT NO ENTER
    // ==========================================
    const formVenda = document.getElementById('formVenda');
    if (formVenda) {
        formVenda.addEventListener('keydown', function(event) {
            if (event.key === 'Enter') {
                if (event.target.tagName === 'TEXTAREA') return;
                event.preventDefault();
                return false;
            }
        });
    }

    // VARIÁVEIS GLOBAIS
    let currentStep = 1;
    const totalSteps = 6;
    
    const btnNext = document.getElementById('btn-next');
    const btnPrev = document.getElementById('btn-prev');
    const btnSubmit = document.getElementById('btn-submit');
    const steps = document.querySelectorAll('.wizard-step');
    const indicators = document.querySelectorAll('.step-indicator');

    // ==========================================
    // 1. VALIDAÇÃO RIGOROSA
    // ==========================================
    function validateStep(step) {
        const currentStepDiv = document.querySelector(`.wizard-step[data-step="${step}"]`);
        const inputs = currentStepDiv.querySelectorAll('input:not(.hidden), select, textarea');
        let isValid = true;
        let errorMessage = '';

        inputs.forEach(inp => {
            if (inp.required && !inp.value && !inp.closest('.hidden')) {
                inp.classList.add('border-red-500', 'ring-1', 'ring-red-500');
                isValid = false;
                errorMessage = 'Preencha todos os campos obrigatórios.';
            } else {
                inp.classList.remove('border-red-500', 'ring-1', 'ring-red-500');
            }
        });

        // Validação CPF/CNPJ (Tamanho mínimo)
        if (step === 1) {
            const tipo = document.querySelector('input[name="tipo_cliente"]:checked').value;
            if (tipo === 'PF') {
                const cpf = document.querySelector('[name="pf_cpf"]').value.replace(/\D/g, '');
                if (cpf.length > 0 && cpf.length < 11) {
                    isValid = false;
                    errorMessage = 'CPF incompleto.';
                    markError('[name="pf_cpf"]');
                }
            } else {
                const cnpj = document.querySelector('[name="pj_cnpj"]').value.replace(/\D/g, '');
                if (cnpj.length > 0 && cnpj.length < 14) {
                    isValid = false;
                    errorMessage = 'CNPJ incompleto.';
                    markError('[name="pj_cnpj"]');
                }
            }
        }

        if (step === 3) {
            const dim1 = parseFloat(document.querySelector('[name="dim_1"]').value);
            const dim2 = parseFloat(document.querySelector('[name="dim_2"]').value);
            if (isNaN(dim1) || dim1 <= 0) { markError('[name="dim_1"]'); isValid = false; }
            if (isNaN(dim2) || dim2 <= 0) { markError('[name="dim_2"]'); isValid = false; }
        }

        if (step === 4) {
            const qtd = parseInt(document.querySelector('[name="qtd_pecas"]').value);
            if (qtd < 1) { markError('[name="qtd_pecas"]'); isValid = false; }
        }

        if (!isValid) {
            alert(errorMessage || 'Verifique os campos marcados em vermelho.');
        }
        return isValid;
    }

    function markError(selector) {
        const el = document.querySelector(selector);
        if(el) el.classList.add('border-red-500', 'ring-1', 'ring-red-500');
    }

    // ==========================================
    // 2. CONTROLE DO WIZARD
    // ==========================================
    function updateWizard() {
        steps.forEach(step => {
            if(parseInt(step.dataset.step) === currentStep) {
                step.classList.remove('hidden');
            } else {
                step.classList.add('hidden');
            }
        });

        indicators.forEach(ind => {
            const stepNum = parseInt(ind.dataset.step);
            ind.classList.remove('bg-navy-900', 'text-white', 'border-navy-900', 'bg-green-500', 'border-green-500');
            
            if (stepNum === currentStep) {
                ind.classList.add('bg-navy-900', 'text-white', 'border-navy-900');
            } else if (stepNum < currentStep) {
                ind.classList.add('bg-green-500', 'text-white', 'border-green-500');
            } else {
                ind.classList.add('bg-gray-100');
            }
        });

        btnPrev.disabled = currentStep === 1;
        
        if (currentStep === totalSteps) {
            btnNext.classList.add('hidden');
            btnSubmit.classList.remove('hidden');
            preencherRevisao();
        } else {
            btnNext.classList.remove('hidden');
            btnSubmit.classList.add('hidden');
        }
    }

    if (btnNext) btnNext.addEventListener('click', () => {
        if(validateStep(currentStep)) { currentStep++; updateWizard(); calculateAll(); }
    });
    if (btnPrev) btnPrev.addEventListener('click', () => { currentStep--; updateWizard(); });

    // ==========================================
    // 3. CÁLCULOS
    // ==========================================
    const inputsCalc = document.querySelectorAll('.input-calc, #select-cor, #select-medida, [name="dim_1"], [name="dim_2"], [name="dim_3"], [name="input_acrescimo"]');
    const selMedida = document.getElementById('select-medida');
    
    if(selMedida) {
        selMedida.addEventListener('change', () => {
            const divDim3 = document.getElementById('div-dim-3');
            const displayUnidade = document.getElementById('display-unidade');
            if(selMedida.value === 'm3') {
                divDim3.classList.remove('hidden');
                displayUnidade.innerText = 'm³';
            } else {
                divDim3.classList.add('hidden');
                displayUnidade.innerText = 'm²';
                document.querySelector('[name="dim_3"]').value = 0;
            }
            calculateAll();
        });
    }

    inputsCalc.forEach(inp => inp.addEventListener('input', calculateAll));
    inputsCalc.forEach(inp => inp.addEventListener('change', calculateAll));

    function calculateAll() {
        const dim1 = parseFloat(document.querySelector('[name="dim_1"]').value) || 0;
        const dim2 = parseFloat(document.querySelector('[name="dim_2"]').value) || 0;
        const dim3 = parseFloat(document.querySelector('[name="dim_3"]').value) || 0;
        const qtd = parseInt(document.querySelector('[name="qtd_pecas"]').value) || 1;
        
        let metragem = 0;
        if(selMedida.value === 'm3') {
            metragem = dim1 * dim2 * (dim3 > 0 ? dim3 : 1);
        } else {
            metragem = dim1 * dim2;
        }
        
        const elDisplayMetragem = document.getElementById('display-metragem');
        const elHiddenMetragem = document.querySelector('[name="metragem_calculada"]');
        if(elDisplayMetragem) elDisplayMetragem.innerText = metragem.toFixed(2);
        if(elHiddenMetragem) elHiddenMetragem.value = metragem;

        const dbCores = (typeof CORES_DB !== 'undefined') ? CORES_DB : [];
        const corId = parseInt(document.getElementById('select-cor').value);
        const corObj = dbCores.find(c => c.id === corId);
        const precoCor = corObj ? corObj.preco : 0;
        
        const elCorPrecoBase = document.getElementById('cor-preco-base');
        if(elCorPrecoBase) elCorPrecoBase.innerText = precoCor.toFixed(2);

        const valorBase = metragem * qtd * precoCor;
        const acrescimo = parseFloat(document.querySelector('[name="input_acrescimo"]').value) || 0;
        const valorComAcrescimo = valorBase + acrescimo;

        let desconto = 0;
        let tipoDesc = 'sem';
        const radioDesc = document.querySelector('input[name="tipo_desconto"]:checked');
        if(radioDesc) tipoDesc = radioDesc.value;

        const valDescInput = parseFloat(document.querySelector('[name="input_desconto"]').value) || 0;

        if (tipoDesc === 'perc') {
            desconto = valorComAcrescimo * (valDescInput / 100);
        } else if (tipoDesc === 'real') {
            desconto = valDescInput;
        }

        let valorFinal = valorComAcrescimo - desconto;
        if (valorFinal < 0) valorFinal = 0;

        updateText('resumo-metragem', `${metragem.toFixed(2)} ${selMedida.value} (x${qtd} pçs)`);
        updateText('resumo-base', valorBase.toFixed(2));
        updateText('resumo-acrescimo', acrescimo.toFixed(2));
        updateText('resumo-desconto', desconto.toFixed(2));
        updateText('resumo-total', valorFinal.toFixed(2));

        const percReal = valorComAcrescimo > 0 ? (desconto / valorComAcrescimo) : 0;
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
    // 4. REVISÃO
    // ==========================================
    window.preencherRevisao = function() {
        const tipo = document.querySelector('input[name="tipo_cliente"]:checked').value;
        let nome = '';
        let solicitante = '-';
        const containerSolicitante = document.getElementById('container-rev-solicitante');
        
        if (tipo === 'PF') {
            nome = document.querySelector('[name="pf_nome"]').value;
            if (containerSolicitante) containerSolicitante.classList.add('hidden');
        } else {
            nome = document.querySelector('[name="pj_fantasia"]').value;
            solicitante = document.querySelector('[name="pj_solicitante"]').value;
            if (containerSolicitante) containerSolicitante.classList.remove('hidden');
        }

        const servico = document.querySelector('[name="descricao_servico"]').value;
        const total = document.getElementById('resumo-total').innerText;
        const selCor = document.getElementById('select-cor');
        const nomeCor = selCor.options[selCor.selectedIndex].text.split('(')[0]; 
        const qtd = document.querySelector('[name="qtd_pecas"]').value;
        const metragemTotal = document.getElementById('display-metragem').innerText;
        
        const dim1 = document.querySelector('[name="dim_1"]').value;
        const dim2 = document.querySelector('[name="dim_2"]').value;
        const dim3 = document.querySelector('[name="dim_3"]').value;
        const tipoMed = document.getElementById('select-medida').value;
        
        let medidasStr = `${dim1} x ${dim2}`;
        if (tipoMed === 'm3') medidasStr += ` x ${dim3}`;
        medidasStr += ` (${tipoMed})`;

        updateText('rev-cliente', nome);
        updateText('rev-solicitante', solicitante);
        updateText('rev-servico', servico);
        updateText('rev-cor', nomeCor);
        updateText('rev-qtd', qtd);
        updateText('rev-medidas', medidasStr);
        updateText('rev-metragem-total', metragemTotal + ' ' + tipoMed);
        updateText('rev-total', total);
    }

    // ==========================================
    // 5. LÓGICA PF/PJ
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
            if (inp.name.includes('nome') || inp.name.includes('fantasia') || inp.name.includes('solicitante')) {
                inp.required = isRequired;
            }
        });
    }
    radiosTipo.forEach(r => r.addEventListener('change', toggleCliente));

    // ==========================================
    // 6. MÁSCARAS DE INPUT (NOVO)
    // ==========================================
    const inpCpf = document.querySelector('[name="pf_cpf"]');
    const inpCnpj = document.querySelector('[name="pj_cnpj"]');

    function mascaraCpf(v) {
        v = v.replace(/\D/g, ""); // Remove tudo que não é dígito
        v = v.substring(0, 11); // Limita tamanho
        v = v.replace(/(\d{3})(\d)/, "$1.$2");
        v = v.replace(/(\d{3})(\d)/, "$1.$2");
        v = v.replace(/(\d{3})(\d{1,2})$/, "$1-$2");
        return v;
    }

    function mascaraCnpj(v) {
        v = v.replace(/\D/g, ""); // Remove tudo que não é dígito
        v = v.substring(0, 14); // Limita tamanho
        v = v.replace(/^(\d{2})(\d)/, "$1.$2");
        v = v.replace(/^(\d{2})\.(\d{3})(\d)/, "$1.$2.$3");
        v = v.replace(/\.(\d{3})(\d)/, ".$1/$2");
        v = v.replace(/(\d{4})(\d)/, "$1-$2");
        return v;
    }

    if (inpCpf) {
        inpCpf.addEventListener('input', function(e) {
            e.target.value = mascaraCpf(e.target.value);
        });
    }

    if (inpCnpj) {
        inpCnpj.addEventListener('input', function(e) {
            e.target.value = mascaraCnpj(e.target.value);
        });
    }

    // Inicialização
    toggleCliente();
    updateWizard();
});