// src/static/js/metas.js

document.addEventListener('DOMContentLoaded', function() {

    // =========================================================================
    // 1. TELA: NOVA META / EDITAR (Calculadora de Dias Úteis em Tempo Real)
    // =========================================================================
    const selectMes = document.getElementById('selectMes');
    const inputAno = document.getElementById('inputAno');
    const inputFeriados = document.getElementById('inputFeriados');
    const checkboxesDias = document.querySelectorAll('.chk-dia');
    const displayDias = document.getElementById('displayDiasUteis');
    const textoResumo = document.getElementById('textoResumoData');

    // Verifica se os elementos da tela de "Nova Meta" existem
    if (selectMes && inputAno && displayDias) {

        /**
         * Função para limpar o campo de feriados:
         * - Remove letras e caracteres especiais.
         * - Impede números maiores que 31.
         */
        function limparInputFeriados(e) {
            let valorOriginal = e.target.value;
            
            // 1. Remove tudo que NÃO for número, vírgula ou espaço
            let valorLimpo = valorOriginal.replace(/[^0-9, ]/g, '');
            
            // 2. Validação Lógica (Números > 31 viram 31)
            // Divide por vírgula para analisar cada número individualmente
            if (valorLimpo) {
                const partes = valorLimpo.split(',');
                const partesCorrigidas = partes.map(parte => {
                    // Mantém espaços para permitir digitação fluida
                    const apenasNumeros = parte.trim();
                    
                    if (apenasNumeros !== '') {
                        const num = parseInt(apenasNumeros);
                        // Se for maior que 31, substitui por 31
                        if (!isNaN(num) && num > 31) {
                            return parte.replace(apenasNumeros, '31'); 
                        }
                    }
                    return parte;
                });
                valorLimpo = partesCorrigidas.join(',');
            }
            
            // Atualiza o campo apenas se houve alteração (evita pular cursor)
            if (valorOriginal !== valorLimpo) {
                e.target.value = valorLimpo;
            }
            
            // Chama o cálculo após limpar
            calcularDiasUteisEmTempoReal();
        }

        /**
         * Função Principal: Calcula quantos dias de trabalho existem no mês
         */
        function calcularDiasUteisEmTempoReal() {
            // A. Captura Mês e Ano
            const mesIndex = parseInt(selectMes.value) - 1; // JS usa meses 0-11
            const ano = parseInt(inputAno.value) || new Date().getFullYear();
            
            // B. Captura Feriados
            const feriadosStr = inputFeriados.value ? inputFeriados.value.split(',') : [];
            const feriados = feriadosStr
                .map(s => parseInt(s.trim()))
                // Filtra apenas números válidos (1 a 31)
                .filter(n => !isNaN(n) && n > 0 && n <= 31);

            // C. Captura Checkboxes Marcados
            // Valores no HTML: '0'=Seg ... '6'=Dom
            const diasSemanaMarcados = Array.from(checkboxesDias)
                .filter(chk => chk.checked)
                .map(chk => chk.value);

            // D. Lógica do Calendário
            const ultimoDiaDoMes = new Date(ano, mesIndex + 1, 0).getDate();
            let contadorUteis = 0;

            for (let dia = 1; dia <= ultimoDiaDoMes; dia++) {
                // Cria data no JS
                const data = new Date(ano, mesIndex, dia);
                const diaSemanaJS = data.getDay(); // 0=Dom, 1=Seg...

                // Converte JS (0=Dom) para Python/Form (6=Dom, 0=Seg)
                let diaParaComparar = (diaSemanaJS === 0) ? '6' : (diaSemanaJS - 1).toString();

                // CONDIÇÃO: Dia da semana marcado E dia do mês não é feriado
                if (diasSemanaMarcados.includes(diaParaComparar) && !feriados.includes(dia)) {
                    contadorUteis++;
                }
            }

            // E. Atualiza Visualização
            displayDias.innerText = contadorUteis;
            
            // Atualiza texto de resumo
            const nomeMes = selectMes.options[selectMes.selectedIndex].text;
            const qtdFeriados = feriados.length;
            
            let texto = `Considerando ${nomeMes}/${ano}`;
            
            // Alerta visual se houver dias inválidos para o mês (ex: 31 de Fevereiro)
            const diasNoMesReal = new Date(ano, mesIndex + 1, 0).getDate();
            const temDiaInvalido = feriados.some(d => d > diasNoMesReal);
            
            if (temDiaInvalido) {
                texto += ` <span class="text-red-500 font-bold" style="font-size: 0.8rem;">(Atenção: Há dias inválidos para este mês!)</span>`;
            } else if (qtdFeriados > 0) {
                texto += ` com ${qtdFeriados} dia(s) de folga extra.`;
            } else {
                texto += ` (sem folgas extras).`;
            }
            textoResumo.innerHTML = texto;

            // Animação de cor no número
            displayDias.classList.remove('text-navy-900');
            displayDias.classList.add('text-blue-600');
            setTimeout(() => {
                displayDias.classList.remove('text-blue-600');
                displayDias.classList.add('text-navy-900');
            }, 200);
        }

        // --- LISTENERS (Ouvintes de Eventos) ---
        // 'input' dispara a cada tecla digitada (ideal para validação imediata)
        inputFeriados.addEventListener('input', limparInputFeriados);
        
        selectMes.addEventListener('change', calcularDiasUteisEmTempoReal);
        inputAno.addEventListener('input', calcularDiasUteisEmTempoReal);
        
        checkboxesDias.forEach(chk => {
            chk.addEventListener('change', calcularDiasUteisEmTempoReal);
        });

        // Executa ao carregar a página
        calcularDiasUteisEmTempoReal();
    }


    // =========================================================================
    // 2. TELA: DISTRIBUIR METAS (Soma dos Vendedores vs Meta Loja)
    // =========================================================================
    const inputsMeta = document.querySelectorAll('.input-meta');
    const valorDistribuidoEl = document.getElementById('valorDistribuido');
    const valorTotalLojaEl = document.getElementById('valorTotalLoja');
    const statusEl = document.getElementById('statusDistribuicao');

    if (inputsMeta.length > 0 && valorDistribuidoEl && valorTotalLojaEl) {
        
        function calcularTotalDistribuicao() {
            let total = 0;
            inputsMeta.forEach(input => {
                total += parseFloat(input.value || 0);
            });

            // Atualiza total formatado
            valorDistribuidoEl.innerText = 'R$ ' + total.toLocaleString('pt-BR', {minimumFractionDigits: 2});
            
            // Compara com a Meta da Loja
            const metaLoja = parseFloat(valorTotalLojaEl.dataset.valor);
            const diff = metaLoja - total;
            
            statusEl.className = ''; 

            if (Math.abs(diff) < 1) {
                statusEl.classList.add('status-ok');
                statusEl.innerText = 'Distribuição Correta (100%)';
            } else if (diff > 0) {
                statusEl.classList.add('status-warning');
                statusEl.innerText = `Faltam R$ ${diff.toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
            } else {
                statusEl.classList.add('status-error');
                statusEl.innerText = `Excedeu R$ ${Math.abs(diff).toLocaleString('pt-BR', {minimumFractionDigits: 2})}`;
            }
        }

        inputsMeta.forEach(input => {
            input.addEventListener('input', calcularTotalDistribuicao);
        });

        calcularTotalDistribuicao();
    }


    // =========================================================================
    // 3. TELA: PAINEL / DASHBOARD (Animação das Barras)
    // =========================================================================
    const barrasProgresso = document.querySelectorAll('.js-progress');
    
    if (barrasProgresso.length > 0) {
        barrasProgresso.forEach(barra => {
            // Lê o atributo data-width (HTML5) para evitar erros de sintaxe no editor
            const larguraAlvo = barra.getAttribute('data-width');
            
            // Aplica o estilo com delay para ativar a transição CSS
            setTimeout(() => {
                barra.style.width = larguraAlvo + '%';
            }, 100);
        });
    }

// =========================================================================
    // 4. MODAL DE DETALHES DE VENDAS (CORRIGIDO)
    // =========================================================================

    const modal = document.getElementById('modalDetalhes');
    const modalContent = document.getElementById('modalContent');
    const modalTitulo = document.getElementById('modalTitulo');
    const loadingModal = document.getElementById('loadingModal');
    const tabelaModal = document.getElementById('tabelaModal');
    const conteudoTabelaModal = document.getElementById('conteudoTabelaModal');
    const vazioModal = document.getElementById('vazioModal');
    
    // Função para fechar o modal
    window.fecharModalDetalhes = function() {
        if(!modal) return;
        modal.classList.add('opacity-0');
        modalContent.classList.remove('scale-100');
        modalContent.classList.add('scale-95');
        setTimeout(() => {
            modal.classList.add('hidden');
        }, 300);
    }

    // Função Lógica (não atrelada ao clique direto)
    function carregarDadosModal(usuarioId, nome, mes, ano) {
        if(!modal) return;

        // Mostrar Modal
        modal.classList.remove('hidden');
        setTimeout(() => {
            modal.classList.remove('opacity-0');
            modalContent.classList.remove('scale-95');
            modalContent.classList.add('scale-100');
        }, 10);
        
        modalTitulo.innerText = `Vendas de ${nome}`;
        loadingModal.classList.remove('hidden');
        tabelaModal.classList.add('hidden');
        vazioModal.classList.add('hidden');
        conteudoTabelaModal.innerHTML = '';

        // Buscar Dados
        fetch(`/metas/api/vendas-usuario/${usuarioId}?mes=${mes}&ano=${ano}`)
            .then(response => response.json())
            .then(data => {
                loadingModal.classList.add('hidden');
                
                if (data.vendas && data.vendas.length > 0) {
                    tabelaModal.classList.remove('hidden');
                    data.vendas.forEach(v => {
                        const row = `
                            <tr class="hover:bg-gray-50 transition-colors">
                                <td class="px-4 py-3 font-mono text-xs text-gray-400">#${v.id}</td>
                                <td class="px-4 py-3 text-gray-600">${v.data}</td>
                                <td class="px-4 py-3 font-medium text-navy-900">${v.cliente}</td>
                                <td class="px-4 py-3 text-right font-bold text-green-600">R$ ${v.valor}</td>
                            </tr>
                        `;
                        conteudoTabelaModal.insertAdjacentHTML('beforeend', row);
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

    // LISTENER AUTOMÁTICO (Esta é a correção para o "onclick")
    // Procura todos os botões com a classe .js-abrir-detalhes e adiciona o evento
    const botoesDetalhes = document.querySelectorAll('.js-abrir-detalhes');
    botoesDetalhes.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault(); // Previne comportamentos padrão
            
            // Lê os dados dos atributos data-
            const id = this.dataset.id;
            const nome = this.dataset.nome;
            const mes = this.dataset.mes;
            const ano = this.dataset.ano;
            
            carregarDadosModal(id, nome, mes, ano);
        });
    });

    // Fechar ao clicar fora
    if(modal) {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                fecharModalDetalhes();
            }
        });
    }

}); // Fim do DOMContentLoaded