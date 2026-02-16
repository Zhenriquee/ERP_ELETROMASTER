// src/static/js/rh_cadastro.js

document.addEventListener('DOMContentLoaded', function() {
    const selectFreq = document.getElementById('selectFreq');
    const inputReal = document.getElementById('inputDiaReal');
    
    // Inputs
    const inputSalario = document.getElementById('salario_base');
    const inputMensal = document.getElementById('inputMensal');
    const selectSemana = document.getElementById('selectDiaSemana');
    const divQuinzenal = document.getElementById('divQuinzenal');
    
    const dia1 = document.getElementById('dia1');
    const dia2 = document.getElementById('dia2');
    const inputPerc = document.getElementById('inputPerc');
    const txtSimulacao = document.getElementById('simulacaoValores');

    if(typeof lucide !== 'undefined') lucide.createIcons();

    function atualizarInterface() {
        const val = selectFreq.value;
        
        // Reset
        if(inputMensal) inputMensal.classList.add('hidden');
        if(selectSemana) selectSemana.classList.add('hidden');
        if(divQuinzenal) {
            divQuinzenal.classList.remove('flex');
            divQuinzenal.classList.add('hidden');
        }

        const valorSalvo = inputReal ? inputReal.value : '';

        if (val === 'semanal') {
            if(selectSemana) {
                selectSemana.classList.remove('hidden');
                selectSemana.value = (valorSalvo.length === 1) ? valorSalvo : '4';
                if(inputReal) inputReal.value = selectSemana.value;
            }
        } 
        else if (val === 'quinzenal') {
            if(divQuinzenal) {
                divQuinzenal.classList.remove('hidden');
                divQuinzenal.classList.add('flex');
                
                if(valorSalvo && valorSalvo.includes(',')) {
                    const partes = valorSalvo.split(',');
                    if(dia1) dia1.value = partes[0];
                    if(dia2) dia2.value = partes[1];
                } else {
                    if(dia1) dia1.value = 15;
                    if(dia2) dia2.value = 30;
                }
                atualizarQuinzenal();
            }
        } 
        else { // mensal
            if(inputMensal) {
                inputMensal.classList.remove('hidden');
                inputMensal.value = (valorSalvo && !valorSalvo.includes(',')) ? valorSalvo : 5;
                if(inputReal) inputReal.value = inputMensal.value;
            }
        }
    }

    // --- CÁLCULO DE SIMULAÇÃO ---
    function simularValores() {
        if (!txtSimulacao || !inputSalario || !inputPerc) return;
        
        const salario = parseFloat(inputSalario.value) || 0;
        const perc = parseInt(inputPerc.value) || 40;
        
        if (salario > 0) {
            const val1 = salario * (perc / 100);
            const val2 = salario - val1;
            
            txtSimulacao.innerHTML = `
                Adiantamento: <strong>R$ ${val1.toFixed(2)}</strong><br>
                Saldo: <strong>R$ ${val2.toFixed(2)}</strong>
            `;
        } else {
            txtSimulacao.innerText = "Informe o salário base.";
        }
    }

    // --- LISTENERS ---
    if(inputMensal) inputMensal.addEventListener('input', function() { if(inputReal) inputReal.value = this.value; });
    if(selectSemana) selectSemana.addEventListener('change', function() { if(inputReal) inputReal.value = this.value; });

    function atualizarQuinzenal() {
        if(dia1 && dia2 && inputReal) {
            inputReal.value = `${dia1.value},${dia2.value}`;
        }
        simularValores();
    }

    if(dia1) dia1.addEventListener('input', atualizarQuinzenal);
    if(dia2) dia2.addEventListener('input', atualizarQuinzenal);
    if(inputPerc) inputPerc.addEventListener('input', simularValores);
    if(inputSalario) inputSalario.addEventListener('input', simularValores);

    if(selectFreq) selectFreq.addEventListener('change', atualizarInterface);

    // Inicializa
    if(selectFreq) atualizarInterface();
});