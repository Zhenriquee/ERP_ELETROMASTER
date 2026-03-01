document.addEventListener('DOMContentLoaded', function() {
    const selectFreq = document.getElementById('selectFreq');
    const inputReal = document.getElementById('inputDiaReal');
    const inputSalario = document.querySelector('.money-mask');
    const form = document.querySelector('form');
    const inputPerc = document.getElementById('inputPerc');
    const txtSimulacao = document.getElementById('simulacaoValores');
    const inputCpf = document.getElementById('cpf');
    const inputPercDesc = document.getElementById('inputPercDesc');

    // 1. MÁSCARA DE MOEDA (Permite digitar R$ 1.000,00)
    if (inputSalario) {
        inputSalario.addEventListener('input', function(e) {
            let value = e.target.value.replace(/\D/g, '');
            if (value === "") { e.target.value = ""; return; }
            
            value = (value / 100).toFixed(2) + '';
            value = value.replace(".", ",");
            value = value.replace(/(\d)(?=(\d{3})+(?!\d))/g, "$1.");
            e.target.value = 'R$ ' + value;
            
            simularValores();
        });
    }

    // 2. LIMPEZA ANTES DE ENVIAR (Remove o R$ para o Python não dar erro)
    if (form && inputSalario) {
        form.addEventListener('submit', function() {
            // Limpa a máscara do Salário (de "R$ 1.621,00" para "1621.00")
            if(inputSalario && inputSalario.value) {
                let rawValue = inputSalario.value.replace("R$ ", "").replace(/\./g, "").replace(",", ".");
                inputSalario.value = rawValue;
            }
            
            // Troca a vírgula do desconto por ponto (de "7,5" para "7.5")
            const inputPercDesc = document.getElementById('inputPercDesc');
            if(inputPercDesc && inputPercDesc.value) {
                inputPercDesc.value = inputPercDesc.value.replace(",", ".");
            }
        });
    }

    // 3. SIMULAÇÃO DE DIVISÃO (40% / 60% do valor informado)
    function simularValores() {
        if (!txtSimulacao || !inputSalario || !inputPerc) return;
        
        let rawValue = inputSalario.value.replace(/\D/g, '');
        const salarioBruto = parseFloat(rawValue) / 100 || 0;
        const percAdiantamento = parseFloat(inputPerc.value) || 40;
        
        const inputPercDesc = document.getElementById('inputPercDesc');
        const percDesconto = parseFloat(inputPercDesc ? inputPercDesc.value.replace(',', '.') : 0) || 0;
        
        if (salarioBruto > 0) {
            const valAdiantamento = salarioBruto * (percAdiantamento / 100);
            const valDesconto = salarioBruto * (percDesconto / 100);
            const valSaldoFinal = salarioBruto - valAdiantamento - valDesconto;
            const liquidoTotal = valAdiantamento + valSaldoFinal;
            
            txtSimulacao.innerHTML = `
                <div class="bg-navy-50 p-4 rounded-xl border border-navy-100 shadow-sm mt-4">
                    <h4 class="text-xs font-bold text-navy-900 mb-3 flex items-center border-b border-navy-200 pb-2 uppercase tracking-wider">
                        <i data-lucide="calculator" class="w-3 h-3 mr-2 text-blue-600"></i> Resumo Líquido
                    </h4>
                    
                    <div class="space-y-2 text-xs">
                        <div class="flex justify-between items-center text-gray-600">
                            <span>Bruto:</span> 
                            <span class="font-medium">R$ ${salarioBruto.toLocaleString('pt-BR', {minimumFractionDigits:2})}</span>
                        </div>
                        
                        <div class="flex justify-between items-center text-red-600">
                            <span>Desconto (${percDesconto}%):</span> 
                            <strong class="font-bold">- R$ ${valDesconto.toLocaleString('pt-BR', {minimumFractionDigits:2})}</strong>
                        </div>
                        
                        <div class="pt-3 mt-2 border-t border-navy-200/60 space-y-2">
                            
                            <div class="bg-white p-3 rounded-lg border border-blue-100 shadow-sm">
                                <div class="text-[10px] font-bold text-blue-500 uppercase mb-1">1ª Quinzena (${percAdiantamento}%)</div>
                                <div class="text-blue-700 font-bold text-sm">R$ ${valAdiantamento.toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                            </div>
                            
                            <div class="bg-white p-3 rounded-lg border border-green-100 shadow-sm">
                                <div class="text-[10px] font-bold text-green-500 uppercase mb-1">2ª Quinzena (Fechamento)</div>
                                <div class="text-green-700 font-bold text-sm">R$ ${valSaldoFinal.toLocaleString('pt-BR', {minimumFractionDigits:2})}</div>
                            </div>
                        </div>

                        <div class="flex justify-between items-center mt-4 pt-3 border-t border-navy-200">
                            <span class="text-[10px] font-bold text-gray-500 uppercase">Total a Receber:</span>
                            <span class="font-black text-navy-900 text-base">R$ ${liquidoTotal.toLocaleString('pt-BR', {minimumFractionDigits:2})}</span>
                        </div>
                    </div>
                </div>
            `;
            
            if(typeof lucide !== 'undefined') lucide.createIcons();
            
        } else {
            txtSimulacao.innerHTML = `
                <div class="p-4 bg-gray-50 border border-dashed border-gray-300 rounded-xl text-center text-xs text-gray-500 mt-4">
                    <i data-lucide="info" class="w-5 h-5 mx-auto mb-2 opacity-50 text-blue-500"></i>
                    <span>Informe o Salário Bruto.</span>
                </div>
            `;
            if(typeof lucide !== 'undefined') lucide.createIcons();
        }
    }

    if(inputPercDesc) inputPercDesc.addEventListener('input', simularValores);

    // 4. MÁSCARA DE CPF
    if (inputCpf) {
        inputCpf.addEventListener('input', function(e) {
            let v = e.target.value.replace(/\D/g,"");
            v = v.replace(/(\d{3})(\d)/,"$1.$2");
            v = v.replace(/(\d{3})(\d)/,"$1.$2");
            v = v.replace(/(\d{3})(\d{1,2})$/,"$1-$2");
            e.target.value = v.substring(0, 14);
        });
    }

    // --- LÓGICA DE INTERFACE (MANTER O QUE JÁ EXISTIA) ---
    const inputMensal = document.getElementById('inputMensal');
    const selectSemana = document.getElementById('selectDiaSemana');
    const divQuinzenal = document.getElementById('divQuinzenal');
    const dia1 = document.getElementById('dia1');
    const dia2 = document.getElementById('dia2');

    function atualizarInterface() {
        const val = selectFreq.value;
        if(inputMensal) inputMensal.classList.add('hidden');
        if(selectSemana) selectSemana.classList.add('hidden');
        if(divQuinzenal) { divQuinzenal.classList.remove('flex'); divQuinzenal.classList.add('hidden'); }

        const valorSalvo = inputReal ? inputReal.value : '';

        if (val === 'semanal') {
            if(selectSemana) {
                selectSemana.classList.remove('hidden');
                selectSemana.value = (valorSalvo.length === 1) ? valorSalvo : '4';
                inputReal.value = selectSemana.value;
            }
        } else if (val === 'quinzenal') {
            if(divQuinzenal) {
                divQuinzenal.classList.remove('hidden'); divQuinzenal.classList.add('flex');
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
        } else {
            if(inputMensal) {
                inputMensal.classList.remove('hidden');
                inputMensal.value = (valorSalvo && !valorSalvo.includes(',')) ? valorSalvo : 5;
                inputReal.value = inputMensal.value;
            }
        }
    }

    function atualizarQuinzenal() {
        if(dia1 && dia2 && inputReal) { inputReal.value = `${dia1.value},${dia2.value}`; }
        simularValores();
    }

    if(inputMensal) inputMensal.addEventListener('input', function() { inputReal.value = this.value; });
    if(selectSemana) selectSemana.addEventListener('change', function() { inputReal.value = this.value; });
    if(dia1) dia1.addEventListener('input', atualizarQuinzenal);
    if(dia2) dia2.addEventListener('input', atualizarQuinzenal);
    if(inputPerc) inputPerc.addEventListener('input', simularValores);
    if(selectFreq) selectFreq.addEventListener('change', atualizarInterface);

    atualizarInterface();
});