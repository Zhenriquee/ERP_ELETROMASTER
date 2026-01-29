// src/static/js/metas.js

document.addEventListener('DOMContentLoaded', function() {
    
    // Inicializa ícones
    if(typeof lucide !== 'undefined') lucide.createIcons();

    // =========================================================================
    // 1. ANIMAÇÃO DE BARRA DE PROGRESSO (PAINEL)
    // =========================================================================
    const barras = document.querySelectorAll('.js-progress');
    if (barras.length > 0) {
        // Pequeno delay para garantir que o navegador renderizou e a transição CSS funcione
        setTimeout(() => {
            barras.forEach(barra => {
                const width = barra.getAttribute('data-width');
                barra.style.width = width + '%';
            });
        }, 300);
    }

    // =========================================================================
    // 2. MODAL DE DETALHES DE VENDAS
    // =========================================================================
    const modal = document.getElementById('modalDetalhes');
    const modalTitulo = document.getElementById('modalTitulo');
    const loadingModal = document.getElementById('loadingModal');
    const tabelaModal = document.getElementById('tabelaModal');
    const conteudoTabelaModal = document.getElementById('conteudoTabelaModal');
    const vazioModal = document.getElementById('vazioModal');

    window.fecharModalDetalhes = function() {
        if(modal) modal.classList.add('hidden');
    }

    function carregarDadosModal(usuarioId, nome, mes, ano) {
        if(!modal) return;
        
        modal.classList.remove('hidden');
        modalTitulo.innerText = `Vendas de ${nome}`;
        
        // Reset estados
        loadingModal.classList.remove('hidden');
        tabelaModal.classList.add('hidden');
        vazioModal.classList.add('hidden');
        conteudoTabelaModal.innerHTML = '';

        // Fetch
        fetch(`/metas/api/vendas-usuario/${usuarioId}?mes=${mes}&ano=${ano}`)
            .then(res => res.json())
            .then(data => {
                loadingModal.classList.add('hidden');
                
                if (data.vendas && data.vendas.length > 0) {
                    tabelaModal.classList.remove('hidden');
                    data.vendas.forEach(v => {
                        const tr = document.createElement('tr');
                        tr.className = "hover:bg-blue-50 transition-colors";
                        tr.innerHTML = `
                            <td class="px-6 py-3 text-gray-500 font-mono text-xs">${v.data.split(' ')[0]}</td>
                            <td class="px-6 py-3 font-bold text-navy-900">${v.cliente}</td>
                            <td class="px-6 py-3 text-right font-bold text-green-600">R$ ${v.valor}</td>
                        `;
                        conteudoTabelaModal.appendChild(tr);
                    });
                } else {
                    vazioModal.classList.remove('hidden');
                }
            })
            .catch(err => {
                console.error(err);
                loadingModal.classList.add('hidden');
                vazioModal.innerText = "Erro ao carregar dados.";
                vazioModal.classList.remove('hidden');
            });
    }

    // Listeners nos botões de abrir
    document.querySelectorAll('.js-abrir-detalhes').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const d = this.dataset;
            carregarDadosModal(d.id, d.nome, d.mes, d.ano);
        });
    });

    // Fechar com ESC
    document.addEventListener('keydown', function(e) {
        if(e.key === 'Escape') fecharModalDetalhes();
    });

    // =========================================================================
    // 3. CÁLCULO DE DIAS ÚTEIS (NOVA META)
    // =========================================================================
    const selectMes = document.getElementById('selectMes');
    const inputAno = document.getElementById('inputAno');
    
    if (selectMes && inputAno) {
        const inputFeriados = document.getElementById('inputFeriados');
        const checkboxes = document.querySelectorAll('.chk-dia');
        const displayDias = document.getElementById('displayDiasUteis');
        const textoResumo = document.getElementById('textoResumoData');

        function calcularDias() {
            const mes = parseInt(selectMes.value) - 1;
            const ano = parseInt(inputAno.value) || new Date().getFullYear();
            
            // Feriados
            const feriados = inputFeriados.value.split(',')
                .map(s => parseInt(s.trim()))
                .filter(n => !isNaN(n) && n > 0 && n <= 31);
            
            // Dias de trabalho (0=Seg ... 6=Dom)
            const diasTrab = Array.from(checkboxes)
                .filter(c => c.checked)
                .map(c => c.value); // Values do form são strings '0'..'6'

            const ultimoDia = new Date(ano, mes + 1, 0).getDate();
            let uteis = 0;

            for (let d = 1; d <= ultimoDia; d++) {
                const date = new Date(ano, mes, d);
                // getDay() do JS retorna 0=Dom, 1=Seg...
                // Precisamos converter para o padrão do Python/Form (0=Seg..6=Dom) ou ajustar a lógica
                // No form.py: 0=Seg, 6=Dom.
                // No JS getDay: 0=Dom, 1=Seg.
                
                let diaSemanaForm = date.getDay() - 1; 
                if (diaSemanaForm === -1) diaSemanaForm = 6; // Domingo vira 6

                if (diasTrab.includes(String(diaSemanaForm)) && !feriados.includes(d)) {
                    uteis++;
                }
            }

            if(displayDias) displayDias.innerText = uteis;
            
            if(textoResumo) {
                const nomeMes = selectMes.options[selectMes.selectedIndex].text;
                textoResumo.innerHTML = `Considerando <strong>${nomeMes}/${ano}</strong> com <strong>${feriados.length}</strong> feriados.`;
            }
        }

        // Listeners
        selectMes.addEventListener('change', calcularDias);
        inputAno.addEventListener('input', calcularDias);
        if(inputFeriados) inputFeriados.addEventListener('input', calcularDias);
        checkboxes.forEach(c => c.addEventListener('change', calcularDias));
        
        // Init
        calcularDias();
    }
    
    // =========================================================================
    // 4. CÁLCULO DE DISTRIBUIÇÃO
    // =========================================================================
    const inputsMeta = document.querySelectorAll('.input-meta');
    const valorDistribuido = document.getElementById('valorDistribuido');
    const valorTotalLoja = document.getElementById('valorTotalLoja');
    const statusDist = document.getElementById('statusDistribuicao');

    if (inputsMeta.length > 0 && valorDistribuido) {
        function calcDistribuicao() {
            let total = 0;
            inputsMeta.forEach(inp => total += parseFloat(inp.value || 0));
            
            valorDistribuido.innerText = 'R$ ' + total.toLocaleString('pt-BR', {minimumFractionDigits: 2});
            
            const meta = parseFloat(valorTotalLoja.dataset.valor);
            const diff = meta - total;

            if(Math.abs(diff) < 1) {
                statusDist.innerHTML = '<span class="text-green-600 font-bold flex items-center"><i data-lucide="check" class="w-4 h-4 mr-1"></i> Distribuição Perfeita</span>';
            } else if (diff > 0) {
                statusDist.innerHTML = `<span class="text-yellow-600 font-bold">Falta distribuir: R$ ${diff.toLocaleString('pt-BR')}</span>`;
            } else {
                statusDist.innerHTML = `<span class="text-red-600 font-bold">Excedeu: R$ ${Math.abs(diff).toLocaleString('pt-BR')}</span>`;
            }
            if(typeof lucide !== 'undefined') lucide.createIcons();
        }

        inputsMeta.forEach(inp => inp.addEventListener('input', calcDistribuicao));
        calcDistribuicao();
    }

});